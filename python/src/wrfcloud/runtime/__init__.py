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
        Initialize the process member variables.
        Override the following values in the sub-classes to incorporate
        error checking for a successful process run.
        Set self.expected_output to a list of file paths (wildcards accepted)
        that will alert us to a failed run if they do not exist.
        Set self.log_file to a string of the path for a log file to read and
        check for a success message, defined by self.log_success_string.
        """
        self.log = Logger(self.__class__.__name__)
        self.success: bool = False
        self.start_time: Union[None, float] = None
        self.end_time: Union[None, float] = None
        self.expected_output: Union[None, List[str]] = None
        self.log_file: Union[None, str] = None
        self.log_success_string: Union[None, str] = None

    def start(self) -> None:
        """
        Start to run the process
        """
        self.start_time = pytz.utc.localize(datetime.utcnow()).timestamp()
        self.success = self.run()
        self.end_time = pytz.utc.localize(datetime.utcnow()).timestamp()
        self.check_success()
        if not self.success:
            self.log.fatal(f'{self.__class__.__name__} failed')

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
        with open(slurm_file, "w") as file_handle:
            file_handle.write('#!/bin/bash\n')
            file_handle.write(f'#SBATCH --job-name={exe_name}\n')
            file_handle.write(f'#SBATCH --ntasks={n_tasks}\n')
            file_handle.write(f'#SBATCH --cpus-per-task=1\n')
            file_handle.write(f'#SBATCH --nodes=1\n')
            file_handle.write(f'#SBATCH --ntasks-per-node={n_tasks}\n')
            file_handle.write(f'#SBATCH --output={exe_name}_%j.log\n')
            file_handle.write(f'\ndate +%s > START\n')
            file_handle.write(f'\n/opt/slurm/bin/srun --mpi=pmi2 {exe_name}\n')
            file_handle.write(f'\ndate +%s > STOP\n')

        # submit the job to the batch queue
        # TODO: get job ID by using subprocess -- os.system returns success status
        self.log.info(f'Submitted {exe_name} to {partition_name}.')
        if os.system(f'/opt/slurm/bin/sbatch -p {partition_name} -W {slurm_file}'):
            self.log.error(f'sbatch returned non-zero')
            return False

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
        Also calls logic to parse logs for success string.
        """
        # if self.run was unsuccessful, don't check expected files or logs
        if not self.success:
            return

        # check if the expected output files exist and error if they do not
        if self.expected_output is None:
            self.log.debug(f'Expected output file check not implemented for {self.__class__.__name__}.')
        else:
            for expected_path in self.expected_output:
                if not glob.glob(expected_path):
                    self.log.error(f'Expected file not found: {expected_path}')
                    self.success = False
                    return

        # parse logs and error if expected string is not found
        self._parse_error_logs()

    def _parse_error_logs(self) -> None:
        """
        Read log file(s) to check for string that indicates a successful run.
        Failure is reported if the log file to check does not exist or if
        the self.log_success_string is not found in the log file.
        Sets self.success to False if a check fails.
        """
        if self.log_file is None:
            self.log.debug(f'Error log parsing not implemented for {self.__class__.__name__}.')
            return

        if not os.path.exists(self.log_file):
            self.log.error(f'Log file does not exist: {self.log_file}')
            self.success = False
            return

        self.log.debug(f'Looking for success string in {self.log_file}')
        with open(self.log_file, 'r') as file_handle:
            output = file_handle.read().splitlines()

        # traverse through file contents backwards
        output.reverse()

        # look for string to indicate a successful run
        for line in output:
            if self.log_success_string in line:
                self.log.debug(f'Success string found in log file: {self.log_success_string}')
                return

        # fail if success string was not found in log file
        self.log.error(f'Success string ({self.log_success_string}) not found in {self.log_file}')
        self.success = False
