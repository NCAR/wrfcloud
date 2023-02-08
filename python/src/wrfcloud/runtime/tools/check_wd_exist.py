"""
Functions for checking if experiment's working directory already exists, and
if it does, taking the action specified by the config file argument "exists"
"""

import os
import shutil
from wrfcloud.log import Logger


def check_wd_exist(exists: str, dir_name: str) -> str:
    """
    check if task's working directory exists and determine the next action
    :param exists: What to do if the directory exists 'skip'|'remove'|'fail'
    :param dir_name: Full path to the directory to check
    :return: 'skip'|'done' or raise exception if directory exists and 'fail' provided
    """
    log = Logger()
    if os.path.isdir(dir_name):
        msg1 = f'Directory already exists: \n                 {dir_name}\n                 '
        if exists == 'skip':
            msg2 = 'Config option set to skip task, returning to main program.'
            log.warn(msg1 + msg2)
            return 'skip'
        elif exists == 'remove':
            msg2 = 'Config option set to remove existing directory.'
            log.warn(msg1 + msg2)
            shutil.rmtree(dir_name)
        else:
            msg2 = 'Move or remove this directory before continuing.'
            log.fatal(msg1 + msg2)
            raise FileExistsError(msg1 + msg2)

    return 'done'
