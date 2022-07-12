#!/usr/bin/env python3

"""
Functions for setting up, executing, and monitoring a run of the WPS program metgrid
"""

import os

# Import our custom modules
from tools.make_wps_namelist import make_wps_namelist


def main(runinfo, logger):
    """Main routine that sets up, runs, and monitors metgrid end-to-end"""
    logger.info(f'Setting up metgrid for "{runinfo.name}"')

    os.mkdir(runinfo.metgriddir)
    os.chdir(runinfo.metgriddir)
    logger.debug('Creating WPS namelist')
    make_wps_namelist(runinfo, logger)

    logger.critical("This script isn't finished yet!")

if __name__ == "__main__":
    print('Script not yet set up for standalone run, exiting...')
