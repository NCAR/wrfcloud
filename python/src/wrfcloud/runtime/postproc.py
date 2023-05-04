"""
Functions for setting up, executing, and monitoring a run of WRF post-processing tasks
"""

import os
import pkgutil
from typing import Union, List
from datetime import timedelta
from f90nml import Namelist
from glob import glob
import yaml
from wrfcloud.jobs import WrfJob
from wrfcloud.jobs.job import WrfLayer
from wrfcloud.runtime import Process
from wrfcloud.log import Logger
from wrfcloud.runtime.tools import check_wd_exist
from wrfcloud.runtime.tools.geojson import automate_geojson_products
from wrfcloud.runtime.tools.vector_json import automate_vector_products
from wrfcloud.runtime.tools.derivations import derive_fields
from wrfcloud.system import get_aws_session


class UPP(Process):
    """
    Class for setting up, executing, and monitoring a run of WRF post-processing tasks
    """
    def __init__(self, job: WrfJob):
        """
        Initialize the ProcProc object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.job = job
        self.namelist: Union[None, Namelist] = None
        self.grib_files: List[str] = []
        self.expected_output = [os.path.join(self.job.upp_dir, 'fhr_*', 'WRFPRS.GrbF*')]

    def _get_files(self) -> None:
        """
        Gets all input files necessary for running unipost.exe
        """
        # get list of files from a configuration file
        upp_files = yaml.safe_load(pkgutil.get_data('wrfcloud', 'runtime/resources/upp_files.yaml'))

        # link static files
        self.log.debug('Linking static files for upp')
        for static_file in upp_files['static_files']:
            target = f'{self.job.upp_code_dir}/{static_file}'
            link = os.path.basename(static_file)
            self.symlink(target, link)

        # link control file
        self.log.debug('Linking control file for upp')
        control_file = upp_files['control_files'][0]
        target = f'{self.job.upp_code_dir}/{control_file}'
        link = 'postxconfig-NT.txt'
        self.symlink(target, link)

        # link satellite fix files
        self.log.debug('Linking satellite fix files for upp')
        for sat_fix_file in upp_files['sat_fix_files']:
            target = f'{self.job.upp_code_dir}/src/lib/crtm2/src/fix/{sat_fix_file}'
            link = os.path.basename(sat_fix_file)
            self.symlink(target, link)

    def _run_upp(self) -> None:
        """
        Executes the unipost.exe program
        """
        self.log.debug('Linking unipost.exe to upp working directory')
        self.symlink(f'{self.job.upp_code_dir}/bin/unipost.exe', 'unipost.exe')

        self.log.debug('Executing unipost.exe')
        if self.job.cores == 1:
            upp_cmd = './unipost.exe >& unipost.log'
            if os.system(upp_cmd):
                self.log.error(f'unipost.exe returned non-zero')
                return False
            return True

        return self.submit_job('unipost.exe', self.job.cores, 'wrf')

    def run(self) -> bool:
        """
        Main routine that sets up, runs, and monitors post-processing end-to-end
        """
        self.log.info(f'Setting up post-processing for "{self.job.job_id}"')

        # Check if experiment working directory already exists,
        # take action based on value of runinfo.exists
        action = check_wd_exist(self.job.exists, self.job.upp_dir)
        if action == "skip":
            return True

        os.makedirs(self.job.upp_dir, exist_ok=True)
        os.chdir(self.job.upp_dir)

        start_date = self.job.start_dt
        end_date = self.job.end_dt
        increment = timedelta(seconds=self.job.output_freq_sec)
        this_date = start_date
        fhr = 0
        while this_date <= end_date:
            # Create subdirs by forecast hour
            fhr_str = ('%03d' % fhr)
            fhr_dir = f'{self.job.upp_dir}/fhr_{fhr_str}'
            os.makedirs(fhr_dir, exist_ok=True)
            os.chdir(fhr_dir)

            # link UPP files
            self.log.debug('Calling get_files')
            self._get_files()

            # Create the itag namelist file for this fhr
            self.log.debug('Creating itag file')
            wrf_date = this_date.strftime("%Y-%m-%d_%H:%M:%S")
            with open('itag', "w") as file_handle:
                file_handle.write(f'{self.job.wrf_dir}/wrfout_d01_{wrf_date}\n')
                file_handle.write("netcdf\n")
                file_handle.write("grib2\n")
                file_handle.write(this_date.strftime("%Y-%m-%d_%H:%M:%S"))
                file_handle.write("\nNCAR\n")

            # run UPP
            self.log.debug('Calling run_upp')
            if not self._run_upp():
                return False

            # collect list of grib files
            try:
                files = glob(f'{fhr_dir}/WRFPRS.GrbF*')
                files.sort()
                grib_file = files[0]
                self.grib_files.append(grib_file)
            except Exception as e:
                self.log.error(f'Failed to find grib file in directory: {fhr_dir}', e)
                return False

            # increment the date and forecast hour
            this_date = this_date + increment
            fhr = fhr + 1

        return True


class Derive(Process):
    """
    Class for deriving products and converting units from WRF output
    """
    def __init__(self, job: WrfJob):
        """
        Initialize the Derive object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.job = job
        self.nc_files = []
        self.expected_output = [
            os.path.join(self.job.derive_dir, 'wrfderive_d0*.nc'),
        ]

    def run(self) -> bool:
        """
        Main routine that sets up and runs field derivations and conversions
        """
        # Check if experiment working directory already exists,
        # take action based on value of runinfo.exists
        action = check_wd_exist(self.job.exists, self.job.derive_dir)
        if action == "skip":
            return True

        # create derive directory
        os.makedirs(self.job.derive_dir, exist_ok=True)

        # get wrf files
        wrf_files = glob(os.path.join(self.job.wrf_dir, 'wrfout*'))

        # derive fields
        for wrf_file in wrf_files:
            self.log.info(f'Deriving fields from {wrf_file}')
            out = derive_fields(in_file=wrf_file, out_dir=self.job.derive_dir)
            if out is None:
                self.log.error(f'Could not derive fields from {wrf_file}')
                return False

            self.log.info(f'Wrote derived file {out}')
            self.nc_files.append(out)

        return True


class GeoJson(Process):
    """
    Class for setting up, executing, and monitoring a run of WRF post-processing tasks
    """
    def __init__(self, job: WrfJob):
        """
        Initialize the ProcProc object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.job: WrfJob = job
        self.namelist: Union[None, Namelist] = None
        self.grib_files: List[str] = []
        self.nc_files: List[str] = []
        self.wrf_layers: List[WrfLayer] = []
        self.expected_output = [
            os.path.join(self.job.derive_dir, 'wrfderive_d0*json.gz'),
            os.path.join(self.job.upp_dir, 'fhr_*', 'WRFPRS.GrbF*.geojson.gz')
        ]

    def set_grib_files(self, grib_files: List[str]) -> None:
        """
        Set the list of GRIB2 files to convert
        :param grib_files: List of files (full path)
        """
        self.grib_files = grib_files

    def set_nc_files(self, nc_files: List[str]) -> None:
        """
        Set the list of NetCDF files to convert
        :param nc_files: List of files (full path)
        """
        self.nc_files = nc_files

    def run(self) -> bool:
        """
        Main routine that sets up, runs, and monitors post-processing end-to-end
        """
        try:
            # create the geojson files
            self._convert_to_layer()

            # upload the geojson/json files to S3
            ok = self._upload_layer_data_files()

            # set the WRF layers in the job
            self.job.layers = self.wrf_layers

            return ok

        except Exception as e:
            self.log.error('Failed to convert and/or upload JSON files.', e)
            return False

    def _convert_to_layer(self) -> None:
        """
        Convert the GRIB2/NetCDF files into GeoJSON files
        :return: List of WRF layer details
        """
        self.wrf_layers = []
        for nc_file in self.nc_files:
            # create layers for contour GeoJSON products
            for wrf_layer in automate_geojson_products(nc_file, 'netcdf'):
                self.wrf_layers.append(wrf_layer)
            # create layers for vector products
            for wrf_layer in automate_vector_products(nc_file):
                self.wrf_layers.append(wrf_layer)
        for grib_file in self.grib_files:
            for wrf_layer in automate_geojson_products(grib_file, 'grib2'):
                self.wrf_layers.append(wrf_layer)

    def _upload_layer_data_files(self) -> bool:
        """
        Upload all geojson files to S3
        :return: True if successful, otherwise False
        """
        # find S3 parameters
        bucket: str = os.environ['WRFCLOUD_BUCKET']
        prefix: str = os.environ['WRF_OUTPUT_PREFIX']

        # get an S3 client
        session = get_aws_session()
        s3 = session.client('s3')

        # upload each file
        upload_count = 0
        for layer in self.wrf_layers:
            # construct the S3 key
            job_id = self.job.job_id
            domain = 'DXX'
            var_name = layer.variable_name
            z_level = layer.z_level if layer.z_level is not None else 0
            file_type = 'json' if layer.plot_type == 'vector' else 'geojson'
            key = f'{prefix}/{job_id}/wrf_{domain}_{layer.dt_str}_{var_name}_{z_level}.{file_type}.gz'
            self.log.debug(f'Uploading s3://{bucket}/{key}')
            # upload the file to an S3 object
            try:
                s3.upload_file(Filename=layer.layer_data, Bucket=bucket, Key=key)
                upload_count += 1
                layer.layer_data = f's3://{bucket}/{key}'
            except Exception as e:
                self.log.warn(f'Failed to upload JSON file: {layer.layer_data}', e)

        # log a message if some files failed to upload
        if upload_count != len(self.wrf_layers):
            self.log.warn(f'Failed to upload all JSON files: {upload_count} of {len(self.wrf_layers)}')

        return upload_count > 0
