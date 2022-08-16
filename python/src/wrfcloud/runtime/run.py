#!/usr/bin/env python3

"""
Wrapper script for creating, submitting, and monitoring runs of the wrfcloud framework.

This script takes a single argument: --name='name' should be set to a unique alphanumeric name
for this particular run of the system. If no name is given, a test configuration will be
run.
"""

import argparse
import logging
import os
import sys

# Import our custom modules
from wrfcloud.runtime import ungrib
from wrfcloud.runtime import metgrid
from wrfcloud.runtime import real
from wrfcloud.runtime import wrf
from wrfcloud.runtime import postproc
from wrfcloud.runtime import RunInfo
from wrfcloud.system import init_environment


# Define our functions
def setup_logging(logdir: str = '.',logfile: str = 'debug.log') -> None:
    """
    Sets up logging, printing high-priority (INFO and higher) messages to screen, and printing all
    messages with detailed timing and routine info in the specified text file. Can be called
    multiple times in a single run (for example, to change logging to a different file path/name)
    """
    logfilename=logdir + '/' + logfile
    logger = logging.getLogger()
    if logging.getLogger().hasHandlers():
        #Delete existing logger handlers
        logging.debug(f'Clearing existing logging settings; new logfile will be {logfilename}')
        logger.handlers.clear()
    try:
        os.makedirs(logdir, exist_ok=True)
    except:
        #Use print() first in case logging has not been set up yet
        print(f'FATAL ERROR: Could not create {logdir} for run logging')
        logging.critical(f'Could not create {logdir} for run logging')
        sys.exit(1)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        filename=logfilename,
                        filemode='a')
    logging.debug(f'Finished setting up debug file logging in {logfilename}')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger().addHandler(console)
    logging.debug('Logging set up successfully')


def main() -> None:
    """Main routine that creates a new run and monitors it through completion"""
    setup_logging(logfile='setup.log')
    logging.debug('Reading command line arguments')
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, default='test',
                        help='"name" should be a unique alphanumeric name for this particular run')
    args = parser.parse_args()
    name = args.name

    logging.info(f'Starting new run "{name}"')
    logging.debug('Creating new RunInfo')
    runinfo = RunInfo(name)
    logging.info(f'Setting up working directory {runinfo.wd}')
    setup_logging(logdir=runinfo.wd, logfile='debug.log')
    logging.debug(f'Moving setup.log to {runinfo.wd}')
    os.rename('setup.log', runinfo.wd + '/setup.log')

    logging.debug('Initialize environment variables for specified configuration')
    init_environment(runinfo.configuration)

    logging.debug('Starting ungrib task')
    ungrib.main(runinfo, logging.getLogger('root.ungrib'))

    logging.debug('Starting metgrid task')
    metgrid.main(runinfo, logging.getLogger('root.metgrid'))

    logging.debug('Starting real task')
    real.main(runinfo, logging.getLogger('root.real'))

    logging.debug('Starting wrf task')
    wrf.main(runinfo, logging.getLogger('root.wrf'))

    logging.debug('Starting postproc task')
    postproc.main(runinfo, logging.getLogger('root.postproc'))


if __name__ == "__main__":
    main()
