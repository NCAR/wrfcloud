"""
Functions for setting up, executing, and monitoring a run of WRF post-processing tasks
"""
from typing import Union
from f90nml import Namelist
from wrfcloud.runtime import RunInfo, Process
from wrfcloud.log import Logger


class PostProc(Process):
    """
    Class for setting up, executing, and monitoring a run of WRF post-processing tasks
    """
    def __init__(self, runinfo: RunInfo):
        """
        Initialize the ProcProc object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.runinfo = runinfo
        self.namelist: Union[None, Namelist] = None

    def run(self) -> bool:
        """
        Main routine that sets up, runs, and monitors post-processing end-to-end
        """
        self.log.info(f'Setting up post-processing for "{self.runinfo.name}"')
        self.log.warn(f"{__name__} isn't fully implemented yet!")

        # TODO: Check for successful completion of postproc
        return True
