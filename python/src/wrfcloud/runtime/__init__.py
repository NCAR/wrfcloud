"""
Shared classes and functions for the WRF runtime
"""

__all__ = ['tools', 'metgrid', 'postproc', 'real', 'run', 'ungrib', 'wrf', 'Process', 'WrfConfig']

import os
import copy
from typing import Union, List
from datetime import datetime
import pytz
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


class WrfConfig:
    """
    Class to contain data representing a WRF model configuration
    """
    # list of all fields supported
    ALL_KEYS: List[str] = ['name', 'description', 's3_key_wrf_namelist', 's3_key_wps_namelist',
                           's3_key_geo_em', 'wrf_namelist', 'wps_namelist', 'cores']

    # list of fields to remove from the data
    SANITIZE_KEYS: List[str] = ['s3_key_wrf_namelist', 's3_key_wps_namelist', 's3_key_geo_em']

    def __init__(self, data: dict = None):
        """
        Initialize the data values
        """
        self.log: Logger = Logger(self.__class__.__name__)
        self.name: Union[str, None] = None
        self.description: Union[str, None] = None
        self.s3_key_wrf_namelist: Union[str, None] = None
        self.s3_key_wps_namelist: Union[str, None] = None
        self.s3_key_geo_em: Union[str, None] = None
        self.wrf_namelist: Union[str, None] = None
        self.wps_namelist: Union[str, None] = None
        self._cores: int = 0

        if data:
            self.data = data

    @property
    def data(self) -> dict:
        """
        Get the data from this object represented as a dictionary
        :return: Data from this object represented as a dictionary
        """
        return {
            'name': self.name,
            's3_key_wrf_namelist':  self.s3_key_wrf_namelist,
            's3_key_wps_namelist': self.s3_key_wps_namelist,
            's3_key_geo_em': self.s3_key_geo_em,
            'wrf_namelist': self.wrf_namelist,
            'wps_namelist': self.wps_namelist,
            'cores': self._cores
        }

    @data.setter
    def data(self, data: dict) -> None:
        """
        Set the object's internal data values to match provided values in the dictionary
        :param data: New values for the object
        """
        self.name = data['name'] if 'name' in data else None
        self.s3_key_wrf_namelist = data['s3_key_wrf_namelist'] if 's3_key_wrf_namelist' in data else None
        self.s3_key_wps_namelist = data['s3_key_wps_namelist'] if 's3_key_wps_namelist' in data else None
        self.s3_key_geo_em = data['s3_key_geo_em'] if 's3_key_geo_em' in data else None
        self.wrf_namelist = data['wrf_namelist'] if 'wrf_namelist' in data else None
        self.wps_namelist = data['wps_namelist'] if 'wps_namelist' in data else None
        self.cores = data['cores'] if 'cores' in data else 0

    @property
    def sanitized_data(self) -> Union[dict, None]:
        """
        Remove any fields that should not be passed back to the user client
        :return: Data dictionary with some fields redacted
        """
        # get a copy of the data dictionary
        data = copy.deepcopy(self.data)

        try:
            # remove all the fields that should not be returned to the user
            for field in self.SANITIZE_KEYS:
                if field in data:
                    data.pop(field)
        except Exception as e:
            self.log.error('Failed to sanitize WRF configuration data', e)
            return None
        return data

    @property
    def cores(self) -> int:
        """
        Get the number of compute cores
        :return: Number of compute cores to use
        """
        return self._cores

    @cores.setter
    def cores(self, core_count: int) -> None:
        """
        Set the number of cores
        :param core_count: Number of cores to use, or <= 0 to calculate number automatically
        """
        self._cores = self._calculate_optimal_core_count() if core_count <= 0 else core_count

    def _calculate_optimal_core_count(self) -> int:
        """
        Calculate the optimal number of cores to use for this configuration
        :return: Number of cores
        """
        self.log.warn('WrfConfig._calculate_optimal_core_count is not implemented.  Returning default 96 cores.')
        return 96
