"""
Functions for setting up, executing, and monitoring a run of the WRF model
"""

import os
import glob
# Import our custom modules
from typing import Union
from f90nml import Namelist
from wrfcloud.runtime import RunInfo, Process
from wrfcloud.log import Logger
from wrfcloud.runtime.tools.check_wd_exist import check_wd_exist


class Wrf(Process):
    """
    Class for setting up, executing, and monitoring a run of the WRF model
    """
    def __init__(self, runinfo: RunInfo):
        """
        Initialize the Wrf object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.runinfo = runinfo
        self.namelist: Union[None, Namelist] = None

    def get_files(self) -> None:
        """
        Gets all input files necessary for running wrf.exe
        """
        self.log.debug('Getting wrfinput and wrfbdy file(s)')

        filelist = glob.glob(f'{self.runinfo.realdir}/wrfinput_d*')
        for initfile in filelist:
            self.symlink(initfile, f'{self.runinfo.wrfdir}/' + os.path.basename(initfile))
        bdyfile=f'{self.runinfo.realdir}/wrfbdy_d01'
        self.symlink(bdyfile, f'{self.runinfo.wrfdir}/' + os.path.basename(bdyfile))

        self.log.debug('Linking namelist.input from real working directory')
        self.symlink(f'{self.runinfo.realdir}/namelist.input', 'namelist.input')

        self.log.debug('Linking other necessary static files')
        static_files = [ 'CAMtr_volume_mixing_ratio',
                         'ozone.formatted',
                         'ozone_lat.formatted',
                         'ozone_plev.formatted',
                         'RRTMG_LW_DATA',
                         'RRTMG_SW_DATA',
                         'GENPARM.TBL',
                         'LANDUSE.TBL',
                         'SOILPARM.TBL',
                         'VEGPARM.TBL' ]

        for statfile in static_files:
            self.symlink(f'{self.runinfo.wrfcodedir}/run/' + statfile, statfile)

    def run_wrf(self) -> None:
        """
        Executes the wrf.exe program
        """
        self.log.debug('Linking wrf.exe to wrf working directory')
        self.symlink(f'{self.runinfo.wrfcodedir}/main/wrf.exe', 'wrf.exe')

        self.log.debug('Executing wrf.exe')
        wrf_cmd = './wrf.exe >& wrf.log'
        os.system(wrf_cmd)

    def run(self) -> bool:
        """Main routine that sets up, runs, and monitors WRF end-to-end"""
        self.log.info(f'Setting up real.exe for "{self.runinfo.name}"')

        #Check if experiment working directory already exists, take action based on value of runinfo.exists
        action = check_wd_exist(self.runinfo.exists,self.runinfo.wrfdir)
        if action == "skip":
            return True

        os.mkdir(self.runinfo.wrfdir)
        os.chdir(self.runinfo.wrfdir)

        self.log.debug('Calling get_files')
        self.get_files()

        self.log.debug('Calling run_wrf')
        self.run_wrf()

        # TODO: Check for successful completion of WRF
        return True
