import os
import requests
import io
import tarfile
import glob
import f90nml

from wrfcloud.system import get_aws_session
from wrfcloud.runtime import RunInfo, Process

# for testing
import argparse
from wrfcloud.system import init_environment
from wrfcloud.log import Logger


class GeoGrid(Process):
    """
    Class to run geogrid to create geo_em file from static terrestrial file
    """

    """
    URL of static terrestrial file used by geogrid
    """
    INPUT_DATA_URL = 'https://www2.mmm.ucar.edu/wrf/src/wps_files/geog_high_res_mandatory.tar.gz'
    EXE = 'geogrid.exe'

    def __init__(self, run_info: RunInfo):
        """
        Construct a geo_em file generator
        :param run_info: RunInfo information about current run
        """
        super().__init__()
        self.run_info: RunInfo = run_info

        # read namelist.wps file from workding dir and read it into Namelist
        nml_file = os.path.join(self.run_info.staticdir, 'namelist.wps')
        with open(nml_file, encoding='utf-8') as nml_file_read:
            self.namelist = f90nml.read(nml_file_read)

        self.data_dir = self.run_info.geogriddir
        self.geogrid_log: str = os.path.join(self.data_dir, 'geogrid.log')

    def run(self):
        """
        Run geogrid.exe and upload geo_em file to S3
        """
        # if any geo_em files already exist, skip running geogrid
        if self._any_geo_em_files_exist_local():
            self.log.info('geo_em files already exist locally. Skip running geogrid')
            return True

        # if geo_em files exist on S3, download them and skip running geogrid
        if self._any_geo_em_files_exist_s3():
            self.log.info('geo_em files already exist on S3. Skip running geogrid')
            return True

        # set up geogrid.exe to run
        self._setup_geogrid()

        # update namelist.wps file with correct geog data path
        self._update_and_write_namelist()

        # download static terrestrial file
        if not self._get_input_file():
            return False

        # run geogrid.exe
        if not self._run_geogrid():
            return False

        # move geo_em output data to static dir
        self._move_geo_em_to_static()

        # send output file to S3
        if not self._upload_geo_em_to_s3():
            return False

        return True

    def _any_geo_em_files_exist_local(self):
        """
        Check of geo_em.dXX.nc files already exist in static data dir
        :returns: True if any files are found, False if not
        """
        check_dir = self.run_info.staticdir
        self.log.debug(f'Checking for geo_em files in {check_dir}')
        for domain in range(1, self.namelist['share']['max_dom'] + 1):
            check_path: str = os.path.join(check_dir, f'geo_em.d{domain:02}.nc')
            self.log.debug(f'Checking if file exists: {check_path}')
            if os.path.exists(check_path):
                return True

        return False

    def _any_geo_em_files_exist_s3(self):
        """
        Check of geo_em.dXX.nc files already exist in static data dir
        :returns: True if any files are found, False if not
        """
        # TODO: get bucket name from WRF info
        bucket_name = 'wrfcloud-output'
        prefix = f'configurations/{self.run_info.name}/'
        self.log.debug(f'Checking for geo_em files on S3 {bucket_name}: {prefix}')
        try:
            s3 = get_aws_session().client('s3')
            geo_em_files = s3.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
            )['Contents']
        except Exception as e:
            self.log.error(f'Failed to get contents of {prefix} on S3', e)
            return False

        files_found = [os.path.basename(obj['Key']) for obj in geo_em_files]
        for domain in range(1, self.namelist['share']['max_dom'] + 1):
            expected_file = f'geo_em.d{domain:02}.nc'
            if expected_file in files_found:
                self.log.info(f'Found {expected_file} on S3')
                # download file
                key = f'{prefix}/{expected_file}'
                filename = os.path.join(self.run_info.staticdir, expected_file)
                self.log.info(f'Downloading {key} to {filename}')
                try:
                    s3.download_file(
                        Bucket=bucket_name,
                        Key=key,
                        Filename=filename,
                    )
                except Exception as e:
                    self.log.error(f'Could not download file from S3: {prefix}/{expected_file}', e)
                    return False
            else:
                self.log.error(f'Could not find file on S3: {prefix}/{expected_file}')
                return False

        return True

    def _setup_geogrid(self):
        """
        Link files into geogrid dir to be able to run geogrid
        """
        # create geogrid data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # unset I_MPI_OFI_PROVIDER environment variable
        self.log.info('Unsetting I_MPI_OFI_PROVIDER so that EFA support is not required')
        if 'I_MPI_OFI_PROVIDER' in os.environ:
            os.environ.pop('I_MPI_OFI_PROVIDER')

        # link geogrid exe and directory into geogrid dir
        self.symlink(os.path.join(self.run_info.wpscodedir, self.EXE),
                     os.path.join(self.data_dir, self.EXE))
        self.symlink(os.path.join(self.run_info.wpscodedir, 'geogrid'),
                     os.path.join(self.data_dir, 'geogrid'))

    def _update_and_write_namelist(self):
        """
        Set geog_data_path in namelist and write modified file to geogrid dir
        """
        # set geog data path to use cluster directory structure
        self.namelist['geogrid']['geog_data_path'] = os.path.join(self.data_dir, 'WPS_GEOG')

        # remove any geogrid variables that start with opt_
        opt_keys = [key for key in self.namelist['geogrid'] if key.startswith('opt_')]
        for key in opt_keys:
            del self.namelist['geogrid'][key]

        # write updated namelist.wps file to geogrid dir
        namelist_out = os.path.join(self.data_dir, 'namelist.wps')
        if os.path.exists(namelist_out):
            self.log.debug(f'Removing existing file before write: {namelist_out}')
            os.remove(namelist_out)
        self.namelist.write(namelist_out)

    def _get_input_file(self):
        """
        Download static terrestrial file and uncompress it
        """
        if os.path.exists(os.path.join(self.data_dir, 'WPS_GEOG')):
            self.log.debug(f'Terrestrial data already exists in {self.data_dir}')
            return True
        self.log.info(f'Downloading terrestrial file: {self.INPUT_DATA_URL}')

        try:
            dl_request = requests.get(self.INPUT_DATA_URL, allow_redirects=True)
            with tarfile.open(fileobj=io.BytesIO(dl_request.content)) as handle:
                handle.extractall(self.data_dir)
        except Exception as e:
            self.log.error(f'Could not obtain terrestrial file: {e}')
            return False

        return True

    def _run_geogrid(self):
        """
        Run geogrid.exe
        """
        self.log.info(f'Running {self.EXE} from {self.data_dir}, '
                      f'logging to {self.geogrid_log}')
        cmd: str = f'cd {self.data_dir}; ./{self.EXE} >& {self.geogrid_log}'
        # if return code is non-zero, return False
        if os.system(cmd):
            self.log.error('geogrid.exe failed')
            return False

        return True

    def _move_geo_em_to_static(self):
        """
        Move geo_em files generated from geogrid.exe to static dir
        """
        for from_name in glob.glob(os.path.join(self.data_dir, f'geo_em.d*.nc')):
            to_name = os.path.join(self.run_info.staticdir, os.path.basename(from_name))
            self.log.info(f'Moving {from_name} to {to_name}')
            os.rename(from_name, to_name)

    def _upload_geo_em_to_s3(self):
        """
        Put output from geogrid on S3
        """
        # TODO: get bucket name from WRF info
        bucket_name = 'wrfcloud-output'
        prefix: str = 'configurations/test'

        for filename in glob.glob(os.path.join(self.run_info.staticdir, f'geo_em.d*.nc')):
            key: str = os.path.basename(filename)

            # upload the data to S3
            self.log.info(f'Uploading {filename} to {bucket_name}/{prefix}/{key}')
            try:
                s3 = get_aws_session().client('s3')
                s3.upload_file(
                    Body=filename,
                    Bucket=bucket_name,
                    Key=f'{prefix}/{key}'
                )
            except Exception as e:
                self.log.error(f'Failed to write {key} data to S3', e)
                return False

        return True

def main() -> None:
    init_environment('cli')
    log = Logger()

    log.debug('Reading command line arguments')
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, default='test',
                        help='"name" should be a unique alphanumeric name for this particular run')
    args = parser.parse_args()
    name = args.name
    log.info(f'Testing geogrid with run "{name}"')
    log.debug('Creating new RunInfo')
    runinfo = RunInfo(name)
    log.info(f'Setting up working directory {runinfo.wd}')
    os.makedirs(runinfo.wd, exist_ok=True)
    log.info('Running geogrid')
    geogrid = GeoGrid(runinfo)
    geogrid.start()
    log.info('Finished geogrid')

if __name__ == "__main__":
    main()
