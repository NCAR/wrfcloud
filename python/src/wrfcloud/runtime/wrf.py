"""
Functions for setting up, executing, and monitoring a run of the WRF model
"""

# Import our custom modules
from typing import Union
from f90nml import Namelist
from wrfcloud.runtime import RunInfo, Process
from wrfcloud.log import Logger


class Wrf(Process):
    """
    Class for setting up, executing, and monitoring a run of the WRF model
    """
    def __init__(self, runinfo: RunInfo):
        """
        Initialize the Wrf object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.runinfo = runinfo
        self.namelist: Union[None, Namelist] = None

    def run(self) -> bool:
        """Main routine that sets up, runs, and monitors WRF end-to-end"""
        self.log.info(f'Setting up WRF for "{self.runinfo.name}"')
        self.log.warn(f'{__name__} is not fully implemented yet!')

        # TODO: Check for successful completion of WRF
        return False
