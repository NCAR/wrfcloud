"""
Functions for setting up, executing, and monitoring a run of the WPS program metgrid
"""

import os
import glob
from typing import Union
from f90nml.namelist import Namelist
from wrfcloud.runtime.tools.make_wps_namelist import make_wps_namelist
from wrfcloud.runtime.tools.check_wd_exist import check_wd_exist
from wrfcloud.runtime import Process
from wrfcloud.jobs import WrfJob
from wrfcloud.log import Logger


class MetGrid(Process):
    """
    Class for setting up, executing, and monitoring a run of the WPS program metgrid
    """

    """
    MetGrid executable filename
    """
    EXE = 'metgrid.exe'

    def __init__(self, job: WrfJob):
        """
        Initialize the MetGrid object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.job = job
        self.namelist: Union[None, Namelist] = None
        self.expected_output = [os.path.join(self.job.metgrid_dir, 'met_em.d0*.nc')]
        self.log_file = os.path.join(self.job.metgrid_dir, 'metgrid.log')
        self.log_success_string = 'Successful completion of program metgrid.exe'

    def get_files(self) -> None:
        """
        Gets all input files necessary for running metgrid
        """
        self.log.debug('Getting geo_em file(s)')
        # Get the number of domains from namelist
        # Assumes geo_em files are in local path/configurations/expn_name. TODO: Make pull from S3
        for domain in range(1, self.namelist['share']['max_dom'] + 1):
            self.symlink(f'{self.job.static_dir}/geo_em.d{domain:02d}.nc', f'geo_em.d{domain:02d}.nc')

        self.log.debug('Linking metgrid dir for tables')
        self.symlink(f'{self.job.wps_code_dir}/metgrid', 'metgrid')

        # Link in the FILES from ungrib
        self.log.debug('Linking FILEs from ungrib step')
        filelist = glob.glob(f'{self.job.ungrib_dir}/FILE*')
        for ungrib_file in filelist:
            self.symlink(ungrib_file, f'{self.job.metgrid_dir}/' + os.path.basename(ungrib_file))

    def run_metgrid(self) -> bool:
        """
        Executes the metgrid.exe program
        """
        self.log.debug(f'Linking {self.EXE} to metgrid working directory')
        self.symlink(f'{self.job.wps_code_dir}/metgrid/{self.EXE}', self.EXE)

        self.log.debug(f'Executing {self.EXE}')
        metgrid_cmd = f'./{self.EXE} >& {os.path.splitext(self.EXE)[0]}.log'
        if os.system(metgrid_cmd):
            self.log.error(f'{self.EXE} returned non-zero')
            return False

        return True

    def run(self) -> bool:
        """
        Main routine that sets up, runs, and monitors metgrid end-to-end
        """
        self.log.info('Unsetting I_MPI_OFI_PROVIDER so that EFA support is not required')
        if 'I_MPI_OFI_PROVIDER' in os.environ:
            os.environ.pop('I_MPI_OFI_PROVIDER')

        self.log.info(f'Setting up metgrid for "{self.job.job_id}"')

        # Check if experiment working directory already exists, take action based on value of runinfo.exists
        action = check_wd_exist(self.job.exists, self.job.metgrid_dir)
        if action == "skip":
            return True

        os.mkdir(self.job.metgrid_dir)
        os.chdir(self.job.metgrid_dir)

        # No longer needed since the whole thing is made in ungrib?
        self.log.debug('Creating WPS namelist')
        self.namelist = make_wps_namelist(self.job)

        self.log.debug('Calling get_files')
        self.get_files()

        self.log.debug('Calling run_metgrid')
        return self.run_metgrid()
