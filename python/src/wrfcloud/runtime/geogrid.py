import os
import requests
import io
import tarfile
import glob
from f90nml.namelist import Namelist

from wrfcloud.system import get_aws_session
from wrfcloud.runtime import RunInfo, Process


class GeoGrid(Process):
    """
    Class to run geogrid to create geo_em file from static terrestrial file
    """

    """
    URL of static terrestrial file used by geogrid
    """
    INPUT_DATA_URL = 'https://www2.mmm.ucar.edu/wrf/src/wps_files/geog_high_res_mandatory.tar.gz'

    def __init__(self, run_info: RunInfo, namelist: Namelist):
        """
        Construct a geo_em file generator
        :param run_info: RunInfo information about current run
        :param namelist: NameList info used to run
        """
        super().__init__()
        self.run_info: RunInfo = run_info
        self.namelist: Namelist = namelist
        self.data_dir = self.run_info.geogriddir
        self.geog_data_path: str = os.path.join(self.data_dir, 'WPS_GEOG')
        self.geogrid_exe: str = os.path.join(self.data_dir, 'geogrid.exe')
        self.geogrid_log: str = os.path.join(self.data_dir, 'geogrid.log')

    def run(self):
        """
        Run geogrid.exe and upload geo_em file to S3
        """
        # if any geo_em files already exist, skip running geogrid
        if self._any_geo_em_files_exist():
            self.log.debug('geo_em files already exist. Skip running geogrid')
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

        # send output file to S3
        if not self._upload_geo_em_to_s3():
            return False

        return True

    def _any_geo_em_files_exist(self):
        """
        Check of geo_em.dXX.nc files already exist in static data dir
        :returns: True if any files are found, False if not
        """
        # TODO: check if files exist on S3 instead of local
        for domain in range(1, self.namelist['share']['max_dom'] + 1):
            check_path: str = os.path.join(self.run_info.staticdir, f'geo_em.d{domain:02}.nc')
            self.log.debug(f'Checking if file exists: {check_path}')
            if os.path.exists(check_path):
                return True
        return False

    def _setup_geogrid(self):
        """
        Link files into geogrid dir to be able to run geogrid
        """
        # create geogrid data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # link geogrid exe and directory into geogrid dir
        self.symlink(os.path.join(self.wpscodedir, 'geogrid.exe'), self.geogrid_exe)
        self.symlink(os.path.join(self.wpscodedir, 'geogrid'),
                     os.path.join(self.data_dir, 'geogrid'))

    def _update_and_write_namelist(self):
        """
        Set geog_data_path in namelist and write modified file to geogrid dir
        """
        # set geog data path to use cluster directory structure
        self.namelist['share']['geog_data_path'] = self.geog_data_path

        # write updated namelist.wps file to geogrid dir
        self.namelist.write(os.path.join(self.data_dir, 'namelist.wps'))

    def _get_input_file(self):
        """
        Download static terrestrial file and uncompress it
        """
        # create geog data path directory if it doesn't exist
        if not os.path.exists(self.geog_data_path):
            os.makedirs(self.geog_data_path)

        self.log.debug(f'Downloading terrestrial file: {self.INPUT_DATA_URL}')

        try:
            dl_request = requests.get(self.INPUT_DATA_URL, allow_redirects=True)
            with tarfile.open(fileobj=io.BytesIO(dl_request.content)) as handle:
                handle.extractall(self.geog_data_path)
        except Exception as e:
            self.log.error(f'Could not obtain terrestrial file: {e}')
            return False

        return True

    def _run_geogrid(self):
        """
        Run geogrid.exe
        """
        self.log.info(f'Running {self.geogrid_exe}, logging to {self.geogrid_log}')
        cmd: str = f'{self.geogrid_exe} >& {self.geogrid_log}'
        # if return code is non-zero, return False
        if os.system(cmd):
            self.log.error('geogrid.exe failed')
            return False

        return True

    def _upload_geo_em_to_s3(self):
        """
        Put output from geogrid on S3
        """
        bucket_name: str = os.environ['WRFCLOUD_BUCKET_NAME']
        prefix: str = 'geo_em'

        for filename in glob.glob(os.path.join(self.run_info.staticdir, f'geo_em.d*.nc')):
            key: str = os.path.basename(filename)

            # upload the data to S3
            self.log.info(f'Uploading {filename} to {bucket_name}/{prefix}/{key}')
            continue
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