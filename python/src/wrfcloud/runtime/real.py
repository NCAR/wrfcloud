"""
Functions for setting up, executing, and monitoring a run of the 'real.exe' WRF pre-processing program
"""
from typing import Union
from f90nml import Namelist
from wrfcloud.runtime import RunInfo, Process
from wrfcloud.log import Logger


class Real(Process):
    """
    Class for setting up, executing, and monitoring a run of the 'real.exe' WRF pre-processing program
    """
    def __init__(self, runinfo: RunInfo):
        """
        Initialize the Real object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.runinfo = runinfo
        self.namelist: Union[None, Namelist] = None

    def run(self) -> bool:
        """
        Main routine that sets up, runs, and monitors real.exe end-to-end
        """
        self.log.info(f'Setting up real.exe for "{self.runinfo.name}"')
        self.log.warn(f'{__name__} is not fully implemented yet!')

        # TODO: Check for successful completion of real
        return False
