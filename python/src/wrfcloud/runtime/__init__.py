__all__ = ['tools', 'metgrid', 'postproc', 'real', 'run', 'ungrib', 'wrf', 'RunInfo']

import os
import logging
import yaml


# Define our Classes
class RunInfo:
    """
    This class keeps info about the run
    """

    def __init__(self, name: str):
        self.name = name
        self.topdir = os.getcwd()
        self.staticdir = self.topdir + '/configurations/' + name
        logging.debug(f'Static data directory is {self.staticdir}')
        self.wpsdir = self.topdir + '/WPSV4/'
        logging.debug(f'WPS directory is {self.wpsdir}')
        self.wrfdir = self.topdir + '/WRFV4/'
        logging.debug(f'WRF directory is {self.wrfdir}')
        self.read_config(name)

        logging.debug(f'Working directory set to {self.wd}')
        self.ungribdir = self.wd + '/ungrib'
        self.metgriddir = self.wd + '/metgrid'

    def read_config(self, name: str) -> None:
        """
        This method reads the config file for this run, and sets the appropriate variables
        for this class.
        """
        config_file = 'run.yml'
        logging.debug(f'reading config file {config_file}')
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            logging.debug(f'Read {config_file} successfully, values are:')
        except IOError:
            logging.warning(f'Could not read config file {config_file}, trying test.yml')
            with open('test.yml', 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            logging.debug('Read test.yml successfully, values are:')
        logging.debug(f'{config}')
        self.configuration = config['run']['configuration']
        self.wd = config['run'].get('workdir','/data/')
        self.startdate = config['run']['start']
        self.enddate = config['run']['end']
        self.input_freq_sec = config['run']['input_freq_sec']
        self.output_freq_sec = config['run']['output_freq_sec']
        self.local_data = config['run']['local_data']
