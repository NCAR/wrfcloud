"""
Functions for setting up, executing, and monitoring a run of the 'real.exe' WRF pre-processing program
"""
import os
import glob
from typing import Union
from f90nml import Namelist
from wrfcloud.runtime import Process
from wrfcloud.jobs import WrfJob
from wrfcloud.log import Logger
from wrfcloud.runtime.tools import make_wrf_namelist
from wrfcloud.runtime.tools import check_wd_exist


class Real(Process):
    """
    Class for setting up, executing, and monitoring a run of the 'real.exe' WRF pre-processing program
    """
    def __init__(self, job: WrfJob):
        """
        Initialize the Real object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.job = job
        self.namelist: Union[None, Namelist] = None

    def get_files(self) -> None:
        """
        Gets all input files necessary for running real.exe
        """
        self.log.debug('Getting met_em file(s)')

        filelist = glob.glob(f'{self.job.metgrid_dir}/met_em*')
        for met_em_file in filelist:
            self.symlink(met_em_file, f'{self.job.real_dir}/' + os.path.basename(met_em_file))

    def run_real(self) -> None:
        """
        Executes the real.exe program
        """
        self.log.debug('Linking real.exe to real working directory')
        self.symlink(f'{self.job.wrf_code_dir}/main/real.exe', 'real.exe')

        self.log.debug('Executing real.exe')
        if self.job.cores == 1:
            real_cmd = './real.exe >& real.log'
            os.system(real_cmd)
        else:
            self.submit_job('real.exe', self.job.cores, 'wrf')

    def run(self) -> bool:
        """
        Main routine that sets up, runs, and monitors real.exe end-to-end
        """
        self.log.info(f'Setting up real.exe for "{self.job.job_id}"')

        # check if experiment working directory already exists
        action = check_wd_exist(self.job.exists, self.job.real_dir)
        if action == "skip":
            return True

        os.mkdir(self.job.real_dir)
        os.chdir(self.job.real_dir)

        # No longer needed since the whole thing is made in ungrib?
        self.log.debug('Creating WRF namelist')
        self.namelist = make_wrf_namelist(self.job)

        self.log.debug('Calling get_files')
        self.get_files()

        self.log.debug('Calling run_real')
        self.run_real()

        # TODO: Check for successful completion of real
        return True
