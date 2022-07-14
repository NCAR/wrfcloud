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
import yaml

# Import our custom modules
from wrfcloud.runtime import ungrib
from wrfcloud.runtime import metgrid
from wrfcloud.runtime import real
from wrfcloud.runtime import wrf
from wrfcloud.runtime import postproc

# Define our Classes
class RunInfo:
    """
    This class keeps info about the run
    """

    def __init__(self, name: str):
        self.name = name
        self.topdir = os.getcwd()
        self.wd = self.topdir + '/' + name
        logging.debug(f'Working directory set to {self.wd}')
        self.staticdir = self.topdir + '/domains/' + name
        logging.debug(f'Static data directory is {self.staticdir}')
        self.read_config(name)

        self.ungribdir = self.wd + '/ungrib'
        self.metgriddir = self.wd + '/metgrid'

    def read_config(self, name: str) -> None:
        """
        This method reads the config file for this run, and sets the appropriate variables
        for this class.
        """
        config_file=name + '.yml'
        logging.debug(f'reading config file {config_file}')
        with open(config_file, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        logging.debug(f'Read {config_file} successfully, values are:')
        logging.debug(f'{config}')
        self.configuration = config['run']['configuration']
        self.startdate = config['run']['start']
        self.enddate = config['run']['end']
        self.input_freq_sec = config['run']['output_freq_sec']
        self.output_freq_sec = config['run']['output_freq_sec']
        self.local_data = config['run']['local_data']


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


def main(name: str) -> None:
    """Main routine that creates a new run and monitors it through completion"""
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, default='test',
                        help='"name" should be a unique alphanumeric name for this particular run')
    args = parser.parse_args()
    main(args.name)