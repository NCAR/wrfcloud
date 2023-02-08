import os
import requests
import io
import tarfile
import glob
import f90nml
from wrfcloud.jobs import WrfJob
from wrfcloud.system import get_aws_session
from wrfcloud.runtime import Process


class GeoGrid(Process):
    """
    Class to run geogrid to create geo_em file from static terrestrial file
    """

    """
    GeoGrid executable filename
    """
    EXE = 'geogrid.exe'

    def __init__(self, job: WrfJob):
        """
        Construct a geo_em file generator
        :param job: RunInfo information about current run
        """
        super().__init__()
        self.job: WrfJob = job
        self.config_dir: str = self.job.static_dir
        self.geogrid_dir: str = self.job.geogrid_dir
        self.run_name: str = self.job.configuration_name
        self.wps_dir: str = self.job.wps_code_dir
        self.bucket_name: str = os.environ['WRFCLOUD_BUCKET']
        self.num_domains: int = 0

    def run(self):
        """
        Run geogrid.exe and upload geo_em file to S3
        :returns: True if geogrid output is available locally, False if not
        """
        # create geogrid data directory if it doesn't exist
        os.makedirs(self.geogrid_dir, exist_ok=True)

        # update namelist.wps file with correct geog data path
        self._update_and_write_namelist()

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
        Check if geo_em.dXX.nc files already exist in static data dir.
        Assumes if one file is found, then all of them are available.
        :returns: True if files are found locally, False if not
        """
        self.log.debug(f'Checking for geo_em files in {self.config_dir}')
        for domain in range(1, self.num_domains + 1):
            check_path: str = os.path.join(self.config_dir, f'geo_em.d{domain:02}.nc')
            self.log.debug(f'Checking if file exists: {check_path}')
            if os.path.exists(check_path):
                return True

        return False

    def _any_geo_em_files_exist_s3(self):
        """
        Check if geo_em.dXX.nc files already exist in S3 bucket and downloads
        them if they are found.
        :returns: True if files were downloaded from S3, False if not
        """
        prefix: str = f'configurations/{self.run_name}'
        self.log.info(f'Checking for geo_em files in s3://{self.bucket_name}/{prefix}')
        try:
            s3 = get_aws_session().client('s3')
            geo_em_files = s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
            )['Contents']
        except Exception as e:
            self.log.error(f'Failed to get contents of {prefix} on S3', e)
            return False

        files_found = [os.path.basename(obj['Key']) for obj in geo_em_files]
        for domain in range(1, self.num_domains + 1):
            expected_file = f'geo_em.d{domain:02}.nc'
            if expected_file in files_found:
                self.log.info(f'Found {expected_file} on S3')
                # download file
                key = f'{prefix}/{expected_file}'
                filename = os.path.join(self.config_dir, expected_file)
                self.log.info(f'Downloading {key} to {filename}')
                try:
                    s3.download_file(
                        Bucket=self.bucket_name,
                        Key=key,
                        Filename=filename,
                    )
                except Exception as e:
                    self.log.error(f'Could not download file from s3://{self.bucket_name}/{prefix}/{expected_file}', e)
                    return False
            else:
                self.log.info(f'Could not find file s3://{self.bucket_name}/{prefix}/{expected_file}')
                return False

        return True

    def _setup_geogrid(self):
        """
        Link files into geogrid dir to be able to run geogrid
        """
        # unset I_MPI_OFI_PROVIDER environment variable
        self.log.info('Unsetting I_MPI_OFI_PROVIDER so that EFA support is not required')
        if 'I_MPI_OFI_PROVIDER' in os.environ:
            os.environ.pop('I_MPI_OFI_PROVIDER')

        # link geogrid exe and directory into geogrid dir
        self.symlink(os.path.join(self.wps_dir, self.EXE),
                     os.path.join(self.geogrid_dir, self.EXE))
        self.symlink(os.path.join(self.wps_dir, 'geogrid'),
                     os.path.join(self.geogrid_dir, 'geogrid'))

    def _update_and_write_namelist(self):
        """
        Set geog_data_path in namelist and write modified file to geogrid dir
        """
        # read namelist.wps file from working dir and read it into Namelist
        nml_file = os.path.join(self.config_dir, 'namelist.wps')
        with open(nml_file, encoding='utf-8') as nml_file_read:
            self.namelist = f90nml.read(nml_file_read)

        # save the number of domains
        self.num_domains = self.namelist['share']['max_dom']

        if 'geogrid' in self.namelist:
            # set geog data path to use cluster directory structure
            self.namelist['geogrid']['geog_data_path'] = os.path.join(self.geogrid_dir, 'WPS_GEOG')

            # remove any geogrid variables that start with opt_
            opt_keys = [key for key in self.namelist['geogrid'] if key.startswith('opt_')]
            for key in opt_keys:
                del self.namelist['geogrid'][key]

        # write updated namelist.wps file to geogrid dir
        namelist_out = os.path.join(self.geogrid_dir, 'namelist.wps')
        if os.path.exists(namelist_out):
            self.log.debug(f'Removing existing file before write: {namelist_out}')
            os.remove(namelist_out)
        self.namelist.write(namelist_out)

    def _get_input_file(self):
        """
        Download static terrestrial file and uncompress it into geogrid dir
        :returns: True if input files were obtained or already exist locally, False if not
        """
        if os.path.exists(os.path.join(self.geogrid_dir, 'WPS_GEOG')):
            self.log.debug(f'Terrestrial data already exists in {self.geogrid_dir}')
            return True

        geogrid_data_url: str = os.environ['GEOGRID_BASE_URL']
        self.log.info(f'Downloading terrestrial file: {geogrid_data_url}')
        try:
            download_request = requests.get(geogrid_data_url, allow_redirects=True)
            with tarfile.open(fileobj=io.BytesIO(download_request.content)) as handle:
                handle.extractall(self.geogrid_dir)
        except Exception as e:
            self.log.error(f'Could not obtain terrestrial file: {e}')
            return False

        return True

    def _run_geogrid(self):
        """
        Run geogrid.exe from geogrid directory
        :returns: True if geogrid.exe runs successfully, False if it fails
        """
        self.log.info(f'Running {self.EXE} from {self.geogrid_dir}, logging to geogrid.log')
        cmd: str = f'cd {self.geogrid_dir}; ./{self.EXE} >& geogrid.log'
        # if return code is non-zero, return False
        if os.system(cmd):
            self.log.error(f'geogrid.exe failed, see {self.geogrid_dir}/geogrid.log')
            return False

        return True

    def _move_geo_em_to_static(self):
        """
        Move geo_em files generated from geogrid.exe to static dir
        """
        for from_name in glob.glob(os.path.join(self.geogrid_dir, f'geo_em.d*.nc')):
            to_name = os.path.join(self.config_dir, os.path.basename(from_name))
            self.log.info(f'Moving {from_name} to {to_name}')
            os.rename(from_name, to_name)

    def _upload_geo_em_to_s3(self):
        """
        Upload geogrid output to S3 bucket
        :returns: True if files were uploaded to S3, False if not
        """
        prefix: str = f'configurations/{self.run_name}'
        self.log.debug(f'Uploading geo_em files to s3://{self.bucket_name}/{prefix}')
        for filename in glob.glob(os.path.join(self.config_dir, f'geo_em.d*.nc')):
            key: str = os.path.basename(filename)

            # upload the data to S3
            self.log.debug(f'Uploading {filename} to s3://{self.bucket_name}/{prefix}/{key}')
            try:
                s3 = get_aws_session().client('s3')
                s3.upload_file(
                    Filename=filename,
                    Bucket=self.bucket_name,
                    Key=f'{prefix}/{key}'
                )
            except Exception as e:
                self.log.error(f'Failed to write {key} data to S3', e)
                return False

        return True
