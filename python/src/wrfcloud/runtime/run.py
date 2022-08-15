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

# Import our custom modules
from wrfcloud.runtime import ungrib
from wrfcloud.runtime import metgrid
from wrfcloud.runtime import real
from wrfcloud.runtime import wrf
from wrfcloud.runtime import postproc
from wrfcloud.runtime import RunInfo


# Define our functions
def setup_logging(logdir: str = '') -> None:
    """
    Sets up logging for a new run. This should be the first action in main() to ensure
    that all actions are properly logged.
    """
    mkdir_fail = False
    try:
        os.mkdir(logdir)
    except:
        mkdir_fail = True
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        filename=logdir + '/debug.log',
                        filemode='a')
    logging.debug('Finished setting up debug file logging')
    if mkdir_fail:
        logging.warning(f'Could not create directory {logdir}')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger().addHandler(console)
    logging.debug('Logging set up successfully')


def main() -> None:
    """Main routine that creates a new run and monitors it through completion"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, default='test',
                        help='"name" should be a unique alphanumeric name for this particular run')
    args = parser.parse_args()
    name = args.name

    setup_logging(name)
    logging.info(f'Starting new run "{name}"')
    logging.debug('Creating new RunInfo')
    runinfo = RunInfo(name)

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
