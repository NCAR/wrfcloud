"""
Module containing common AWS operations for NCAR/RAL
"""

import os

__all__ = [
    'api',
    'aws',
    'config',
    'dynamodb',
    'user',
    'log',
    'system',
    'runtime',
    'jobs',
    'setup'
]


def get_package_info(info):
    """
    Get info about package such as version number and release date
    :param info name of file in package to read
    :return string containing requested info
    """
    filename = os.path.abspath(os.path.join(os.path.dirname(__file__), info))
    with open(filename, 'r') as file_handle:
        version = file_handle.read().strip()
    return version


__version__ = get_package_info('VERSION')
__release_date__ = get_package_info('RELEASE_DATE')
