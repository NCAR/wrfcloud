"""
Shared classes and functions for the WRF runtime
"""

__all__ = ['run', 'tools', 'geogrid', 'ungrib', 'metgrid', 'real', 'wrf', 'postproc', 'Process']

import os
from typing import Union
from datetime import datetime
import pytz
import glob

from wrfcloud.log import Logger


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
        self.expected_output: Union[None, list] = None
        self.error_logs = None
        self.log_file: Union[None, str] = None

    def start(self) -> None:
        """
        Start to run the process
        """
        self.start_time = pytz.utc.localize(datetime.utcnow()).timestamp()
        self.success = self.run()
        self.check_success()
        self.end_time = pytz.utc.localize(datetime.utcnow()).timestamp()

    def get_run_summary(self) -> str:
        """
        Get a summary of the run as a string that can be logged
        :return: Summary of the run: elapsed time and success flag
        """
        return f'{self.__class__.__name__} {"succeeded" if self.success else "failed"} in ' \
               f'{self.get_elapsed_time()} seconds.'

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
        Create a symlink on the file system. This function will raise
        an exception if the original file or directory does not exist
        :param target: Path to the file or directory that already exists and will be pointed to by the new symlink
        :param link: Path to the new symlink that will be created
        """
        if not os.path.isdir(target) and not os.path.isfile(target):
            self.log.error(f'Failed to create symlink from {target} to {link}')
            raise FileNotFoundError(f'{target} does not exist')
        # remove sym link if it already exists
        if os.path.islink(link):
            self.log.debug(f'Removing existing sym link before creating new link: {link}')
            os.unlink(link)
        os.symlink(target, link)
        return True

    def submit_job(self, exe_name: str, n_tasks: int, partition_name: str) -> bool:
        """
        Create a job card file and submit it to the slurm scheduler
        :param exe_name: Name of executable
        :param n_tasks: Int number of MPI tasks
        :param partition_name: Partition name
        :return: True if successfully submitted to the batch queue
        """
        slurm_file = exe_name + ".sbatch"
        f = open(slurm_file, "w")
        f.write('#!/bin/bash\n')
        f.write(f'#SBATCH --job-name={exe_name}\n')
        f.write(f'#SBATCH --ntasks={n_tasks}\n')
        f.write(f'#SBATCH --cpus-per-task=1\n')
        f.write(f'#SBATCH --nodes=1\n')
        f.write(f'#SBATCH --ntasks-per-node={n_tasks}\n')
        f.write(f'#SBATCH --output={exe_name}_%j.log\n')
        f.write(f'\ndate +%s > START\n')
        f.write(f'\n/opt/slurm/bin/srun --mpi=pmi2 {exe_name}\n')
        f.write(f'\ndate +%s > STOP\n')
        f.close()

        # submit the job to the batch queue
        slurm_job_id = os.system(f'/opt/slurm/bin/sbatch -p {partition_name} -W {slurm_file}')
        self.log.info(f'Submitted {exe_name} to {partition_name} as job {slurm_job_id}.')

        return True

    def run(self) -> bool:
        """
        Abstract method
        """
        self.log.error('run is an abstract method on {self.__class__} and should not be called directly.')
        return False

    def check_success(self) -> None:
        """
        Check expected output files and logs to ensure run was successful.
        """
        # if self.run was unsuccessful, don't check for expected files
        if not self.success:
            details = self.parse_error_logs()
            self.log.fatal(f'{self.__class__.__name__} failed', details=details)
            return

        if self.expected_output is None:
            self.log.debug(f'Error checking not implemented for {self.__class__.__name__}.')
            self.success = True
            return

        for expected_path in self.expected_output:
            if not glob.glob(expected_path):
                details = f'Expected file not found: {expected_path}\n'
                details += self.parse_error_logs()
                self.log.fatal(f'{self.__class__.__name__} failed', details=details)
                self.success = False
                return
        self.success = True
        return

    def parse_error_logs(self) -> str:
        """
        Read log file(s) on error to pass useful information to user.
        Each subclass of Process should implement its own logic by
        overriding this function.
        """
        if self.log_file is None:
            self.log.debug(f'Error log parsing not implemented for {self.__class__.__name__}.')
            return ''
        if not os.path.exists(self.log_file):
            return f'Log file does not exist: {self.log_file}'
        output = f'*****\nContent from log file: {self.log_file}\n*****\n\n'
        with open(self.log_file, 'r') as file_handle:
            output += file_handle.read()
        return output
