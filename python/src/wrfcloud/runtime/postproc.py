"""
Functions for setting up, executing, and monitoring a run of WRF post-processing tasks
"""

import os
import pkgutil
from typing import Union
from datetime import datetime, timedelta
import yaml
from f90nml import Namelist
from wrfcloud.runtime import RunInfo, Process
from wrfcloud.log import Logger
from wrfcloud.runtime.tools import check_wd_exist


class PostProc(Process):
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

            # increment the date and forecast hour
            this_date = this_date + increment
            fhr = fhr + 1

        # TODO: Check for successful completion of postproc
        return True
