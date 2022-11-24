"""
Functions for setting up, executing, and monitoring a run of WRF post-processing tasks
"""

import os
import pkgutil
from typing import Union, List
from datetime import datetime, timedelta
import yaml
from f90nml import Namelist

from wrfcloud.jobs import WrfJob
from wrfcloud.jobs.job import WrfLayer
from wrfcloud.runtime import RunInfo, Process
from wrfcloud.log import Logger
from wrfcloud.runtime.tools import check_wd_exist
from wrfcloud.runtime.tools.geojson import automate_geojson_products
from wrfcloud.system import get_aws_session


class UPP(Process):
    """
    Class for setting up, executing, and monitoring a run of WRF post-processing tasks
    """
    def __init__(self, runinfo: RunInfo):
        """
        Initialize the ProcProc object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.runinfo = runinfo
        self.namelist: Union[None, Namelist] = None
        self.grib_files: List[str] = []

    def _get_files(self) -> None:
        """
        Gets all input files necessary for running unipost.exe
        """
        # get list of files from a configuration file
        upp_files = yaml.safe_load(pkgutil.get_data('wrfcloud', 'runtime/resources/upp_files.yaml'))

        # link static files
        self.log.debug('Linking static files for upp')
        for static_file in upp_files['static_files']:
            target = f'{self.runinfo.uppcodedir}/' + static_file
            link = os.path.basename(static_file)
            self.symlink(target, link)

        # link control file
        self.log.debug('Linking control file for upp')
        control_file = upp_files['control_files'][0]
        target = f'{self.runinfo.uppcodedir}/{control_file}'
        link = 'postxconfig-NT.txt'
        self.symlink(target, link)

        # link satellite fix files
        self.log.debug('Linking satellite fix files for upp')
        for sat_fix_file in upp_files['sat_fix_files']:
            target = f'{self.runinfo.uppcodedir}/src/lib/crtm2/src/fix/' + sat_fix_file
            link = os.path.basename(sat_fix_file)
            self.symlink(target, link)

    def _run_upp(self) -> None:
        """
        Executes the unipost.exe program
        """
        self.log.debug('Linking unipost.exe to upp working directory')
        self.symlink(f'{self.runinfo.uppcodedir}/bin/unipost.exe', 'unipost.exe')

        self.log.debug('Executing unipost.exe')
        if self.runinfo.wrfcores == 1:
            upp_cmd = './unipost.exe >& unipost.log'
            os.system(upp_cmd)
        else:
            self.submit_job('unipost.exe', self.runinfo.wrfcores, 'wrf')

    def run(self) -> bool:
        """
        Main routine that sets up, runs, and monitors post-processing end-to-end
        """
        self.log.info(f'Setting up post-processing for "{self.runinfo.name}"')

        # Check if experiment working directory already exists,
        # take action based on value of runinfo.exists
        action = check_wd_exist(self.runinfo.exists, self.runinfo.uppdir)
        if action == "skip":
            return True

        os.makedirs(self.runinfo.uppdir)
        os.chdir(self.runinfo.uppdir)

        startdate = datetime.strptime(self.runinfo.startdate, '%Y-%m-%d_%H:%M:%S')
        enddate = datetime.strptime(self.runinfo.enddate, '%Y-%m-%d_%H:%M:%S')
        increment = timedelta(seconds=self.runinfo.output_freq_sec)
        this_date = startdate
        fhr = 0
        while this_date <= enddate:
            # Create subdirs by forecast hour
            fhrstr = ('%03d' % fhr)
            fhrdir = f'{self.runinfo.uppdir}/fhr_{fhrstr}'
            os.makedirs(fhrdir)
            os.chdir(fhrdir)

            # link UPP files
            self.log.debug('Calling get_files')
            self._get_files()

            # Create the itag namelist file for this fhr
            self.log.debug('Creating itag file')
            wrf_date = this_date.strftime("%Y-%m-%d_%H:%M:%S")
            f = open('itag', "w")
            f.write(f'{self.runinfo.wrfdir}/wrfout_d01_{wrf_date}\n')
            f.write("netcdf\n")
            f.write("grib2\n")
            f.write(this_date.strftime("%Y-%m-%d_%H:%M:%S"))
            f.write("\nNCAR\n")
            f.close()

            # run UPP
            self.log.debug('Calling run_upp')
            self._run_upp()

            # create list of grib files
            self.grib_files.append(f'{fhrdir}/WRFPRS.GrbF{fhrstr[1:]}')

            # increment the date and forecast hour
            this_date = this_date + increment
            fhr = fhr + 1

        # TODO: Check for successful completion of postproc
        return True


class GeoJson(Process):
    """
    Class for setting up, executing, and monitoring a run of WRF post-processing tasks
    """
    def __init__(self, runinfo: RunInfo, job: WrfJob):
        """
        Initialize the ProcProc object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.runinfo = runinfo
        self.job: WrfJob = job
        self.namelist: Union[None, Namelist] = None
        self.grib_files: List[str] = []
        self.wrf_layers: List[WrfLayer] = []

    def set_grib_files(self, grib_files: List[str]) -> None:
        """
        Set the list of GRIB2 files to convert
        :param grib_files: List of files (full path)
        """
        self.grib_files = grib_files

    def run(self) -> bool:
        """
        Main routine that sets up, runs, and monitors post-processing end-to-end
        """
        try:
            # create the geojson files
            self._convert_to_geojson()

            # upload the geojson files to S3
            ok = self._upload_geojson_files()

            # set the WRF layers in the job
            self.job.layers = self.wrf_layers

            return ok

        except Exception as e:
            self.log.error('Failed to convert and/or upload GeoJSON files.', e)
            return False

    def _convert_to_geojson(self) -> None:
        """
        Convert the GRIB2 files into GeoJSON files
        :return: List of WRF layer details
        """
        self.wrf_layers = []
        for grib_file in self.grib_files:
            for wrf_layer in automate_geojson_products(grib_file, 'grib2'):
                self.wrf_layers.append(wrf_layer)

    def _upload_geojson_files(self) -> bool:
        """
        Upload all geojson files to S3
        :return: True if successful, otherwise False
        """
        # find S3 parameters
        bucket: str = os.environ['WRF_OUTPUT_BUCKET']
        prefix: str = os.environ['WRF_OUTPUT_PREFIX']

        # get an S3 client
        session = get_aws_session()
        s3 = session.client('s3')

        # upload each file
        upload_count = 0
        for layer in self.wrf_layers:
            # TODO: The date/time should be set on the layer once the information is available in the GRIB2 files
            layer.dt = self.runinfo.start_datetime.timestamp() + (layer.time_step * self.runinfo.output_freq_sec)

            # construct the S3 key
            job_id = self.job.job_id
            domain = 'DXX'
            var_name = layer.variable_name
            z_level = layer.z_level if layer.z_level is not None else 0
            key = f'{prefix}/{job_id}/wrf_{domain}_{layer.dt_str}_{var_name}_{z_level}.geojson.gz'

            # upload the file to an S3 object
            try:
                s3.upload_file(Filename=layer.layer_data, Bucket=bucket, Key=key)
                upload_count += 1
                layer.layer_data = f's3://{bucket}/{key}'
            except Exception as e:
                self.log.warn(f'Failed to upload GeoJSON file: {layer.layer_data}', e)

        # log a message if some files failed to upload
        if upload_count != len(self.wrf_layers):
            self.log.warn(f'Failed to upload all GeoJSON files: {upload_count} of {len(self.wrf_layers)}')

        return upload_count > 0
