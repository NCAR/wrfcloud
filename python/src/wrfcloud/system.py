"""
This module contains global variables and functions.  Values are not set by default.  The user
must call 'init_environment(...)' to initialize variables.  Any environment variables with the
same name will be overwritten.
"""

import os
import sys
import pkgutil
import yaml


# App
APP_NAME = None
SYSTEM_EMAIL_SENDER = None
SYSTEM_EMAIL_RECEIVER = None
LANGUAGE = None

# AWS Account Profile
AWS_PROFILE = ''
AWS_REGION = ''

# API Gateway Options
API_URL = None
APP_URL = None
API_STAGE = None
ALLOW_CORS = None

# DynamoDB Options
SESSION_TABLE_NAME = None
USER_TABLE_NAME = None
ENDPOINT_URL = None

# Logging options
LOG_LEVEL = None
LOG_FORMAT = None

# The environment that has been set
ENVIRONMENT = None


def init_environment(env='test'):
    """
    Initialize the environment variables
    :return: None
    """
    global ENVIRONMENT
    ENVIRONMENT = env

    from wrfcloud.log import Logger
    log = Logger()
    log.info('Initializing %s environment' % ENVIRONMENT)

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


def get_aws_session():
    """
    Get an AWS session with the correct keys
    :return: AWS session
    """
    import boto3
    return boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
