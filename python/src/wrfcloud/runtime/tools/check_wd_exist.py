#!/usr/bin/env python3

"""
Functions for checking if experiment's working directory already exists, and
if it does, taking the action specified by the config file argument "exists"
"""

import os
import shutil
from wrfcloud.log import Logger


def check_wd_exist(exists: str, dirname : str) -> str:
    """Main routine that checks if task's working directory exists, and depending
       on the value of runinfo.exists, takes an action:
       skip:    Return string "skip"
       remove:  Removes the existing working directory and returns string "done"
       [else]:  Any other string defaults to previous behavior, which raises an exception.
       """

    log = Logger()
    if os.path.isdir(dirname):
        msg1 = f'Directory already exists: \n                 {dirname}\n                 '
        if exists == 'skip':
            msg2 = 'Config option set to skip task, returning to main program.'
            log.warn(msg1 + msg2)
            return 'skip'
        elif exists == 'remove':
            msg2 = 'Config option set to remove existing directory.'
            log.warn(msg1 + msg2)
            shutil.rmtree(dirname)
        else:
            msg2 = 'Move or remove this directory before continuing.'
            log.fatal(msg1 + msg2)
            raise FileExistsError(msg1 + msg2)

    return 'done'
