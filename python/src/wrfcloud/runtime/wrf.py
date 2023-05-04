"""
Functions for setting up, executing, and monitoring a run of the WRF model
"""

import os
import glob
from typing import Union
from f90nml import Namelist
from wrfcloud.runtime import Process
from wrfcloud.jobs import WrfJob
from wrfcloud.log import Logger
from wrfcloud.runtime.tools import check_wd_exist


class Wrf(Process):
    """
    Class for setting up, executing, and monitoring a run of the WRF model
    """
    def __init__(self, job: WrfJob):
        """
        Initialize the Wrf object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.job = job
        self.namelist: Union[None, Namelist] = None
        self.expected_output = [os.path.join(self.job.wrf_dir, 'wrfout_d0*')]
        self.log_file = os.path.join(self.job.wrf_dir, 'rsl.out.0000')

    def get_files(self) -> None:
        """
        Gets all input files necessary for running wrf.exe
        """
        self.log.debug('Getting wrfinput and wrfbdy file(s)')

        filelist = glob.glob(f'{self.job.real_dir}/wrfinput_d*')
        for init_file in filelist:
            self.symlink(init_file, f'{self.job.wrf_dir}/' + os.path.basename(init_file))
        body_file = f'{self.job.real_dir}/wrfbdy_d01'
        self.symlink(body_file, f'{self.job.wrf_dir}/' + os.path.basename(body_file))

        # link to other files in the WRF run directory
        self.log.debug('Linking other necessary static files')
        static_files = glob.glob(f'{self.job.wrf_code_dir}/run/*[!.exe|namelist.input]')
        for static_file in static_files:
            self.symlink(static_file, static_file.split('/')[-1])

        # link the namelist file to the run directory
        self.log.debug('Linking namelist.input from real working directory')
        self.symlink(f'{self.job.real_dir}/namelist.input', 'namelist.input')

    def run_wrf(self) -> None:
        """
        Executes the wrf.exe program
        """
        self.log.debug('Linking wrf.exe to wrf working directory')
        self.symlink(f'{self.job.wrf_code_dir}/main/wrf.exe', 'wrf.exe')

        self.log.debug('Executing wrf.exe')
        if self.job.cores == 1:
            wrf_cmd = './wrf.exe >& wrf.log'
            os.system(wrf_cmd)
        else:
            self.submit_job('wrf.exe', self.job.cores, 'wrf')

    def run(self) -> bool:
        """Main routine that sets up, runs, and monitors WRF end-to-end"""
        self.log.info(f'Setting up wrf.exe for "{self.job.job_id}"')

        # Check if experiment working directory already exists, take action based on value of runinfo.exists
        action = check_wd_exist(self.job.exists, self.job.wrf_dir)
        if action == "skip":
            return True

        os.mkdir(self.job.wrf_dir)
        os.chdir(self.job.wrf_dir)

        self.log.debug('Calling get_files')
        self.get_files()

        self.log.debug('Calling run_wrf')
        self.run_wrf()

        # TODO: Check for successful completion of WRF
        return True
