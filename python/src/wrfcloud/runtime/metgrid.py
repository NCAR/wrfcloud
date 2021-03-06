#!/usr/bin/env python3

"""
Functions for setting up, executing, and monitoring a run of the WPS program metgrid
"""

import os
from logging import Logger

# Import our custom modules
from wrfcloud.runtime.tools.make_wps_namelist import make_wps_namelist
from wrfcloud.runtime import RunInfo


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
    logger.debug('Creating WPS namelist')
    make_wps_namelist(runinfo, logger)

    logger.warning(f"{__name__} isn't fully implemented yet!")


if __name__ == "__main__":
    print('Script not yet set up for standalone run, exiting...')
