"""
Functions for setting up, executing, and monitoring a run of the WPS program metgrid
"""

import os
import glob
from typing import Union
from f90nml.namelist import Namelist
from wrfcloud.runtime.tools.make_wps_namelist import make_wps_namelist
from wrfcloud.runtime.tools.check_wd_exist import check_wd_exist
from wrfcloud.runtime import RunInfo, Process
from wrfcloud.log import Logger


class MetGrid(Process):
    """
    Class for setting up, executing, and monitoring a run of the WPS program metgrid
    """
    def __init__(self, runinfo: RunInfo):
        """
        Initialize the MetGrid object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.runinfo = runinfo
        self.namelist: Union[None, Namelist] = None

    def get_files(self) -> None:
        """
        Gets all input files necessary for running metgrid
        """
        self.log.debug('Getting geo_em file(s)')
        # Get the number of domains from namelist
        # Assumes geo_em files are in local path/configurations/expn_name. TODO: Make pull from S3
        for domain in range(1, self.namelist['share']['max_dom'] + 1):
            self.symlink(f'{self.runinfo.staticdir}/geo_em.d{domain:02d}.nc', f'geo_em.d{domain:02d}.nc')

        self.log.debug('Linking metgrid dir for tables')
        self.symlink(f'{self.runinfo.wpscodedir}/metgrid', 'metgrid')

        # Link in the FILES from ungrib
        self.log.debug('Linking FILEs from ungrib step')
        filelist = glob.glob(f'{self.runinfo.ungribdir}/FILE*')
        for ungribfile in filelist:
            self.symlink(ungribfile, f'{self.runinfo.metgriddir}/' + os.path.basename(ungribfile))

    def run_metgrid(self) -> None:
        """
        Executes the metgrid.exe program
        """
        self.log.debug('Linking metgrid.exe to metgrid working directory')
        self.symlink(f'{self.runinfo.wpscodedir}/metgrid/metgrid.exe', 'metgrid.exe')

        self.log.debug('Executing metgrid.exe')
        metgrid_cmd = './metgrid.exe >& metgrid.log'
        os.system(metgrid_cmd)

    def run(self) -> bool:
        """
        Main routine that sets up, runs, and monitors metgrid end-to-end
        """
        self.log.info(f'Setting up metgrid for "{self.runinfo.name}"')

        #Check if experiment working directory already exists, take action based on value of runinfo.exists
        action = check_wd_exist(self.runinfo.exists,self.runinfo.metgriddir)
        if action == "skip":
            return True

        os.mkdir(self.runinfo.metgriddir)
        os.chdir(self.runinfo.metgriddir)

        # No longer needed since the whole thing is made in ungrib?
        self.log.debug('Creating WPS namelist')
        self.namelist = make_wps_namelist(self.runinfo)

        self.log.debug('Calling get_files')
        self.get_files()

        self.log.debug('Calling run_metgrid')
        self.run_metgrid()

        # TODO: Check for successful completion of metgrid
        return True


if __name__ == "__main__":
    print('Script not yet set up for standalone run, exiting...')
