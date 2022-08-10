#!/usr/bin/env python3

"""
Functions for setting up, executing, and monitoring a run of the WPS program ungrib
"""

import datetime
import os
from logging import Logger
from f90nml.namelist import Namelist

# Import our custom modules
from wrfcloud.runtime.tools.make_wps_namelist import make_wps_namelist
from wrfcloud.runtime.tools.get_grib_input import get_grib_input
from wrfcloud.runtime import RunInfo

def get_files(runinfo: RunInfo, logger: Logger, namelist: Namelist) -> None:
    """Gets all input files necessary for running ungrib"""

    logger.debug('Getting GRIB input files')
    get_grib_input(runinfo, logger)

    logger.debug('Getting geo_em file(s)')
    # Get the number of domains from namelist
    # Assumes geo_em files are in local path/domains/expn_name. TODO: Make pull from S3
    for domain in range(1, namelist['share']['max_dom'] + 1):
        os.symlink(f'{runinfo.staticdir}/geo_em.d{domain:02d}.nc', f'geo_em.d{domain:02d}.nc')

    logger.debug('Getting VTable.GFS')
    os.symlink(f'{runinfo.wpsdir}/ungrib/Variable_Tables/Vtable.GFS', 'Vtable')


def run_ungrib(runinfo: RunInfo, logger: Logger, namelist: Namelist) -> None:
    """Executes the ungrib.exe program"""
    logger.debug('Linking ungrib.exe to ungrib working directory')
    os.symlink(f'{runinfo.wpsdir}/ungrib/ungrib.exe', 'ungrib.exe')

    logger.debug('Executing ungrib.exe')
    ungrib_cmd ='./ungrib.exe >& ungrib.log'
    os.system(ungrib_cmd)
 

def main(runinfo: RunInfo, logger: Logger) -> None:
    """Main routine that sets up, runs, and monitors ungrib end-to-end"""
    logger.info(f'Setting up ungrib for "{runinfo.name}"')

    # Stop execution if experiment working directory already exists
    if os.path.isdir(runinfo.ungribdir):
        errmsg = (f"Ungrib directory \n                 {runinfo.ungribdir}\n                 "
                  "already exists. Move or remove this directory before continuing.")
        logger.critical(errmsg)
        raise FileExistsError(errmsg)

    os.mkdir(runinfo.ungribdir)
    os.chdir(runinfo.ungribdir)

    logger.debug('Creating WPS namelist')
    namelist = make_wps_namelist(runinfo, logger)

    logger.debug('Getting ungrib input files')
    get_files(runinfo, logger, namelist)

    logger.debug('Calling run_ungrib')
    run_ungrib(runinfo, logger, namelist)


if __name__ == "__main__":
    print('Script not yet set up for standalone run, exiting...')
