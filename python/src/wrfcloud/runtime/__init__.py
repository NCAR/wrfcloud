"""
Shared classes and functions for the WRF runtime
"""

__all__ = ['tools', 'metgrid', 'postproc', 'real', 'run', 'ungrib', 'wrf', 'RunInfo', 'Process']

import os
from typing import Union
from datetime import datetime
import yaml
import pytz
from wrfcloud.log import Logger


class RunInfo:
    """
    This class keeps info about the run
    """

    def __init__(self, name: str):
        """
        Initialize the RunInfo object
        """
        self.log = Logger(self.__class__.__name__)
        self.name = name
        self.topdir = os.getcwd()
        self.staticdir = self.topdir + '/configurations/' + name
        self.log.debug(f'Static data directory is {self.staticdir}')
        self.read_config(name)

        self.log.debug(f'Working directory set to {self.wd}')
        self.ungribdir = self.wd + '/ungrib'
        self.metgriddir = self.wd + '/metgrid'
        self.realdir = self.wd + '/real'
        self.wrfdir = self.wd + '/wrf'

    def read_config(self, name: str) -> None:
        """
        This method reads the config file for this run, and sets the appropriate variables
        for this class.
        """
        config_file = 'run.yml'
        self.log.debug(f'reading config file {config_file}')
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            self.log.debug(f'Read {config_file} successfully, values are:')
        except IOError:
            self.log.warn(f'Could not read config file {config_file}, trying test.yml')
            with open('test.yml', 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            self.log.debug('Read test.yml successfully, values are:')
        self.log.debug(f'{config}')
        self.config= config
        self.wpscodedir = config['static'].get('wpscodedir',self.topdir + '/WPSV4/')
        self.log.debug(f'WPS code directory is {self.wpscodedir}')
        self.wrfcodedir = config['static'].get('wrfcodedir',self.topdir + '/WRFV4/')
        self.log.debug(f'WRF code directory is {self.wrfcodedir}')
        self.configuration = config['run']['configuration']
        self.wd = config['run'].get('workdir', '/data/')

        #Extract individual date/time components from startdate and enddate for later use
        self.startdate = config['run']['start']
        self.enddate = config['run']['end']
        split_startdate = self.startdate.split('-')
        split_enddate = self.enddate.split('-')
        self.startyear = split_startdate[0]
        self.startmonth = split_startdate[1]
        self.startday = split_startdate[2][0:2]
        self.starthour = split_startdate[2][3:5]
        self.endyear = split_enddate[0]
        self.endmonth = split_enddate[1]
        self.endday = split_enddate[2][0:2]
        self.endhour = split_enddate[2][3:5]

        #Calculate runtime in hours
        date_format_str = '%Y-%m-%d_%H:%M:%S'
        start = datetime.strptime(self.startdate, date_format_str)
        end =   datetime.strptime(self.enddate, date_format_str)
        # Get interval between two timstamps as timedelta object
        diff = end - start
        # Get interval between two timstamps in hours
        self.runhours = diff.total_seconds() / 3600

        self.input_freq_sec = config['run']['input_freq_sec']
        self.output_freq_sec = config['run']['output_freq_sec']
        self.output_freq_min = self.output_freq_sec / 60

        self.local_data = config['run'].get('local_data', '')
        self.exists = config['run'].get('exists', '')
        # If "exists" is not set or invalid, set behavior to die
        if self.exists not in ["overwrite", "remove", "save", "skip"]:
            self.exists = 'die'


class Process:
    """
    A generic process in the WRF processing
    """
    def __init__(self):
        """
        Initialize the process member variables
        """
        self.log = Logger(self.__class__.__name__)
        self.success: bool = False
        self.start_time: Union[None, float] = None
        self.end_time: Union[None, float] = None

    def start(self) -> None:
        """
        Start to run the process
        """
        self.start_time = pytz.utc.localize(datetime.utcnow()).timestamp()
        self.success = self.run()
        self.end_time = pytz.utc.localize(datetime.utcnow()).timestamp()

    def get_run_summary(self) -> str:
        """
        Get a summary of the run as a string that can be logged
        :return: Summary of the run: elapsed time and success flag
        """
        return f'{self.__class__.__name__} {"succeeded" if self.success else "failed"} in {self.get_elapsed_time()} seconds.'

    def get_elapsed_time(self) -> Union[None, float]:
        """
        Get the elapsed time of the run, or None if the process has not run or finished yet.
        :return: Elapsed time of the process run in seconds
        """
        if self.start_time is None or self.end_time is None:
            return None
        return self.end_time - self.start_time

    def symlink(self, target: str, link: str) -> bool:
        """
        Create a symlink on the file system. This function will raise an exception
        if the original file or directory does not exist.
        :param target: Path to the file or directory that already exists and will be pointed to by the new symlink
        :param link: Path to the new symlink that will be created
        """
        if not os.path.isdir(target) and not os.path.isfile(target):
            self.log.error(f'Failed to create symlink from {target} to {link}')
            raise FileNotFoundError(f'{target} does not exist')
        os.symlink(target, link)
        return True

    def run(self) -> bool:
        """
        Abstract method
        """
        self.log.error('run is an abstract method on {self.__class__} and should not be called directly.')
        return False
