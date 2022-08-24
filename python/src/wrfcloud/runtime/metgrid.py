"""
Functions for setting up, executing, and monitoring a run of the WPS program metgrid
"""

import os
import glob
from typing import Union
from f90nml.namelist import Namelist
from wrfcloud.runtime.tools.make_wps_namelist import make_wps_namelist
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
        Gets all input files necessary for running ungrib
        """
        self.log.debug('Getting geo_em file(s)')
        # Get the number of domains from namelist
        # Assumes geo_em files are in local path/configurations/expn_name. TODO: Make pull from S3
        for domain in range(1, self.namelist['share']['max_dom'] + 1):
            os.symlink(f'{self.runinfo.staticdir}/geo_em.d{domain:02d}.nc', f'geo_em.d{domain:02d}.nc')

        self.log.debug('Linking metgrid dir for tables')
        os.symlink(f'{self.runinfo.wpsdir}/metgrid', 'metgrid')

        # Link in the FILES from ungrib
        self.log.debug('Linking FILEs from ungrib step')
        filelist = glob.glob(f'{self.runinfo.ungribdir}/FILE*')
        for ungribfile in filelist:
            os.symlink(ungribfile, f'{self.runinfo.metgriddir}/' + os.path.basename(ungribfile))

    def run_metgrid(self) -> None:
        """
        Executes the metgrid.exe program
        """
        self.log.debug('Linking metgrid.exe to metgrid working directory')
        os.symlink(f'{self.runinfo.wpsdir}/metgrid/metgrid.exe', 'metgrid.exe')

        self.log.debug('Executing metgrid.exe')
        metgrid_cmd = './metgrid.exe >& metgrid.log'
        os.system(metgrid_cmd)

    def run(self) -> None:
        """
        Main routine that sets up, runs, and monitors metgrid end-to-end
        """
        self.log.info(f'Setting up metgrid for "{self.runinfo.name}"')

        # Stop execution if experiment working directory already exists
        if os.path.isdir(self.runinfo.metgriddir):
            errmsg = (f"Metgrid directory \n                 {self.runinfo.metgriddir}\n                 "
                      "already exists. Move or remove this directory before continuing.")
            err = FileExistsError(errmsg)
            self.log.fatal(errmsg, err)
            raise FileExistsError(errmsg)

        os.mkdir(self.runinfo.metgriddir)
        os.chdir(self.runinfo.metgriddir)

        # No longer needed since the whole thing is made in ungrib?
        self.log.debug('Creating WPS namelist')
        self.namelist = make_wps_namelist(self.runinfo)

        self.log.debug('Calling get_files')
        self.get_files()

        self.log.debug('Calling run_metgrid')
        self.run_metgrid()


if __name__ == "__main__":
    print('Script not yet set up for standalone run, exiting...')
