#!/usr/bin/env python3

"""
Functions for setting up, executing, and monitoring a run of the WPS program ungrib
"""

import os
import glob
import itertools
from string import ascii_uppercase

# Import our custom modules
from wrfcloud.runtime.tools.make_wps_namelist import make_wps_namelist

def get_grib_input(runinfo, logger, namelist):
    """
    Gets GRIB files for processing by ungrib

    If user has specified local data (or this is the test case), will attempt to read from that
    local data.

    Otherwise, will attempt to grab data from NOAA S3 bucket
    https://registry.opendata.aws/noaa-gfs-bdp-pds/
    """
    logger.debug(f'test')

    if runinfo.local_data:
        logger.debug('Getting GRIB file(s) from local source')
        # Iterator for generating letter strings for GRIBFILE suffixes. Don't blame me, this is ungrib's fault
        suffixes = itertools.product(ascii_uppercase, repeat=3)
        filelist = []
        # If runinfo.local_data is a string, convert it to a list
        if isinstance(runinfo.local_data, str):
            data = [runinfo.local_data]
        else:
            data = runinfo.local_data

        for entry in data:
            #Since there may be multiple string entries in runinfo.local_data, we need to parse
            #each one individually using glob.glob, then append them all together
            filelist.extend(sorted(glob.glob(entry)))
        for gribfile in filelist:
            # Gives us GRIBFILE.AAA on first iteration, then GRIBFILE.AAB, GRIBFILE.AAC, etc.
            griblink = 'GRIBFILE.' + "".join(suffixes.__next__())
            logger.debug(f'Linking input GRIB file {gribfile} to {griblink}')
            os.symlink(gribfile,griblink)
    else:
        logger.debug('Getting GRIB file(s) from S3 bucket')
        logger.warning('Not yet implemented!')

def get_files(runinfo, logger, namelist):
    """Gets all input files necessary for running ungrib"""

    logger.debug('Getting GRIB input files')
    get_grib_input(runinfo, logger, namelist)

    logger.debug('Getting geo_em file(s)')
    # Get the number of domains from namelist
    for domain in range(1,namelist['share']['max_dom'] + 1):
        os.symlink(f'{runinfo.staticdir}/geo_em.d{domain:02d}.nc',f'geo_em.d{domain:02d}.nc')

    logger.debug('Getting VTable')
    

def main(runinfo, logger):
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

    logger.warning(f"{__name__} isn't fully implemented yet!")

if __name__ == "__main__":
    print('Script not yet set up for standalone run, exiting...')
