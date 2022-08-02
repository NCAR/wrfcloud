#!/usr/bin/env python3

"""
Functions for setting up, executing, and monitoring a run of the WPS program metgrid
"""

import os
import glob
from logging import Logger
from f90nml.namelist import Namelist

# Import our custom modules
from wrfcloud.runtime.tools.make_wps_namelist import make_wps_namelist
from wrfcloud.runtime import RunInfo


def get_files(runinfo: RunInfo, logger: Logger, namelist: Namelist) -> None:
    """Gets all input files necessary for running ungrib"""

    logger.debug('Getting geo_em file(s)')
    # Get the number of domains from namelist
    # Assumes geo_em files are in local path/domains/expn_name. TODO: Make pull from S3
    for domain in range(1, namelist['share']['max_dom'] + 1):
        os.symlink(f'{runinfo.staticdir}/geo_em.d{domain:02d}.nc', f'geo_em.d{domain:02d}.nc')

    logger.debug('Linking metgrid dir for tables')
    os.symlink(f'{runinfo.wpsdir}/metgrid', 'metgrid')

    # Link in the FILES from ungrib
    logger.debug('Linking FILEs from ungrib step')
    filelist = glob.glob(f'{runinfo.ungribdir}/FILE*') 
    for ungribfile in filelist:
        print(ungribfile)
        os.symlink(ungribfile, f'{runinfo.metgriddir}/' + os.path.basename(ungribfile))


def run_metgrid(runinfo: RunInfo, logger: Logger, namelist: Namelist) -> None:
    """Executes the metgrid.exe program"""

    logger.debug('Linking metgrid.exe to metgrid working directory')
    os.symlink(f'{runinfo.wpsdir}/metgrid/metgrid.exe', 'metgrid.exe')

    logger.debug('Executing metgrid.exe')
    metgrid_cmd = './metgrid.exe >& metgrid.log'
    os.system(metgrid_cmd)


def main(runinfo: RunInfo, logger: Logger) -> None:
    """Main routine that sets up, runs, and monitors metgrid end-to-end"""
    logger.info(f'Setting up metgrid for "{runinfo.name}"')

    # Stop execution if experiment working directory already exists
    if os.path.isdir(runinfo.metgriddir):
        errmsg = (f"Metgrid directory \n                 {runinfo.metgriddir}\n                 "
                   "already exists. Move or remove this directory before continuing.")
        logger.critical(errmsg)
        raise FileExistsError(errmsg)

    os.mkdir(runinfo.metgriddir)
    os.chdir(runinfo.metgriddir)
   
    # No longer needed since the whole thing is made in ungrib? 
    logger.debug('Creating WPS namelist')
    namelist = make_wps_namelist(runinfo, logger)

    logger.debug('Calling get_files')
    get_files(runinfo, logger, namelist)

    logger.debug('Calling run_metgrid')
    run_metgrid(runinfo, logger, namelist)


if __name__ == "__main__":
    print('Script not yet set up for standalone run, exiting...')
