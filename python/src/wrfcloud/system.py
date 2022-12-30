"""
This module contains global variables and functions.  Values are not set by default.  The user
must call 'init_environment(...)' to initialize variables.  Any environment variables with the
same name will be overwritten.
"""

import os
import sys
import pkgutil
import yaml
from wrfcloud.log import LogLevel

# App
APP_NAME = None
LANGUAGE = None

# AWS Account Profile
AWS_PROFILE = ''
AWS_REGION = ''

# The environment that has been set
ENVIRONMENT = None


def init_environment(env='test'):
    """
    Initialize the environment variables
    :return: None
    """
    global ENVIRONMENT
    ENVIRONMENT = env

    # create a logger with default options
    from wrfcloud.log import Logger
    log = Logger()
    log.info('Initializing %s environment' % ENVIRONMENT)

    # load the requested environment
    data = yaml.full_load(pkgutil.get_data('wrfcloud', 'resources/env_vars.yaml'))
    module = sys.modules[__name__]
    for key in data[env]:
        if data[env][key] == 'None':
            if key in os.environ:
                os.environ.pop(key)
            setattr(module, key, None)
        else:
            os.environ[key] = str(data[env][key])
            setattr(module, key, data[env][key])

    # reset default logging parameters from the initialized environment
    if 'LOG_LEVEL' in os.environ:
        Logger.LOG_LEVEL = LogLevel.log_level_to_int(os.environ['LOG_LEVEL'])
    if 'LOG_FORMAT' in os.environ:
        Logger.LOG_FORMAT = os.environ['LOG_FORMAT']
    if 'LOG_APPLICATION_NAME' in os.environ:
        Logger.APPLICATION_NAME = os.environ['LOG_APPLICATION_NAME']


def get_aws_session(region: str = None, profile: str = None):
    """
    Get an AWS session with the correct keys
    :param region: Optional AWS region name (e.g. us-west-2)
    :param profile: Optional AWS profile name available in credentials file
    :return: AWS session
    """
    import boto3

    region = region if region is not None else AWS_REGION
    profile = profile if profile is not None else AWS_PROFILE

    if profile is not None and profile != '' and region is not None and region != '':
        return boto3.Session(profile_name=profile, region_name=region)
    elif profile is not None and profile != '':
        return boto3.Session(profile_name=profile)
    elif profile is not None and region != '':
        return boto3.Session(region_name=region)
    else:
        return boto3.Session()
