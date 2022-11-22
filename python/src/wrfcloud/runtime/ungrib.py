"""
Class for setting up, executing, and monitoring a run of the WPS program ungrib
"""

import glob
import itertools
import os
from string import ascii_uppercase
from typing import Union
from f90nml.namelist import Namelist
from wrfcloud.runtime.tools.make_wps_namelist import make_wps_namelist
from wrfcloud.runtime.tools.get_grib_input import get_grib_input
from wrfcloud.runtime.tools.check_wd_exist import check_wd_exist
from wrfcloud.runtime import RunInfo, Process
from wrfcloud.log import Logger


class Ungrib(Process):
    """
    Class for setting up, executing, and monitoring a run of the WPS program ungrib
    """
    def __init__(self, runinfo: RunInfo):
        """
        Initialize the Ungrib object
        """
        super().__init__()
        self.log: Logger = Logger(self.__class__.__name__)
        self.runinfo: RunInfo = runinfo
        self.namelist: Union[None, Namelist] = None

    def get_files(self) -> None:
        """
        Gets all input files necessary for running ungrib
        """
        suffixes = itertools.product(ascii_uppercase, repeat=3)
        if self.runinfo.local_data:
            self.log.debug('Getting GRIB file(s) from specified local directory(ies)')
            filelist = []
            # If runinfo.local_data is a string, convert it to a list
            if isinstance(self.runinfo.local_data, str):
                data = [self.runinfo.local_data]
            else:
                data = self.runinfo.local_data

            for entry in data:
                # Since there may be multiple string entries in runinfo.local_data, we need to parse
                # each one individually using glob.glob, then append them all together
                filelist.extend(sorted(glob.glob(entry)))
        else:
            self.log.debug('"local_data" not set; getting GRIB file(s) from remote source')
            get_grib_input(self.runinfo)
            filelist = sorted(glob.glob(os.path.join(self.runinfo.ungribdir, 'gfs.*')))

        if not filelist:
            self.log.error('List of input files is empty; check configuration')
            raise FileNotFoundError('No input files found')

        for gribfile in filelist:
            # Gives us GRIBFILE.AAA on first iteration, then GRIBFILE.AAB, GRIBFILE.AAC, etc.
            griblink = 'GRIBFILE.' + "".join(suffixes.__next__())
            self.log.debug(f'Linking input GRIB file {gribfile} to {griblink}')
            self.symlink(gribfile, griblink)

        self.log.debug('Getting geo_em file(s)')
        # Get the number of domains from namelist
        # Assumes geo_em files are in local path/configurations/expn_name. TODO: Make pull from S3
        for domain in range(1, self.namelist['share']['max_dom'] + 1):
            self.symlink(f'{self.runinfo.staticdir}/geo_em.d{domain:02d}.nc', f'geo_em.d{domain:02d}.nc')

        self.log.debug('Getting VTable.GFS')
        self.symlink(f'{self.runinfo.wpscodedir}/ungrib/Variable_Tables/Vtable.GFS', 'Vtable')

    def run_ungrib(self) -> None:
        """Executes the ungrib.exe program"""
        self.log.debug('Linking ungrib.exe to ungrib working directory')
        self.symlink(f'{self.runinfo.wpscodedir}/ungrib/ungrib.exe', 'ungrib.exe')

        self.log.debug('Executing ungrib.exe')
        ungrib_cmd = './ungrib.exe >& ungrib.log'
        os.system(ungrib_cmd)

    def run(self) -> bool:
        """Main routine that sets up, runs, and monitors ungrib end-to-end"""
        self.log.info(f'Setting up ungrib for "{self.runinfo.name}"')

        # check if experiment working directory already exists, take action based on value of runinfo.exists
        action = check_wd_exist(self.runinfo.exists,self.runinfo.ungribdir)
        if action == "skip":
            return True

        os.mkdir(self.runinfo.ungribdir)
        os.chdir(self.runinfo.ungribdir)

        self.log.debug('Creating WPS namelist')
        self.namelist = make_wps_namelist(self.runinfo)

        self.log.debug('Getting ungrib input files')
        self.get_files()

        self.log.debug('Calling run_ungrib')
        self.run_ungrib()

        # TODO: Check for successful completion of ungrib
        return True


if __name__ == "__main__":
    print('Script not yet set up for standalone run, exiting...')
