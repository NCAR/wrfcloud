"""
Functions for setting up, executing, and monitoring a run of the 'real.exe' WRF pre-processing program
"""
import os
import glob
from typing import Union
from f90nml import Namelist
from wrfcloud.runtime import RunInfo, Process
from wrfcloud.log import Logger
from wrfcloud.runtime.tools import make_wrf_namelist
from wrfcloud.runtime.tools import check_wd_exist


class Real(Process):
    """
    Class for setting up, executing, and monitoring a run of the 'real.exe' WRF pre-processing program
    """
    def __init__(self, runinfo: RunInfo):
        """
        Initialize the Real object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.runinfo = runinfo
        self.namelist: Union[None, Namelist] = None

    def get_files(self) -> None:
        """
        Gets all input files necessary for running real.exe
        """
        self.log.debug('Getting met_em file(s)')

        filelist = glob.glob(f'{self.runinfo.metgriddir}/met_em*')
        for metemfile in filelist:
            self.symlink(metemfile, f'{self.runinfo.realdir}/' + os.path.basename(metemfile))

    def run_real(self) -> None:
        """
        Executes the real.exe program
        """
        self.log.debug('Linking real.exe to real working directory')
        self.symlink(f'{self.runinfo.wrfcodedir}/main/real.exe', 'real.exe')

        self.log.debug('Executing real.exe')
        real_cmd = './real.exe >& real.log'
        os.system(real_cmd)

    def run(self) -> bool:
        """
        Main routine that sets up, runs, and monitors real.exe end-to-end
        """
        self.log.info(f'Setting up real.exe for "{self.runinfo.name}"')

        #Check if experiment working directory already exists, take action based on value of runinfo.exists
        action = check_wd_exist(self.runinfo.exists,self.runinfo.realdir)
        if action == "skip":
            return True

        os.mkdir(self.runinfo.realdir)
        os.chdir(self.runinfo.realdir)

        # No longer needed since the whole thing is made in ungrib?
        self.log.debug('Creating WRF namelist')
        self.namelist = make_wrf_namelist(self.runinfo)

        self.log.debug('Calling get_files')
        self.get_files()

        self.log.debug('Calling run_real')
        self.run_real()

        # TODO: Check for successful completion of real
        return True
