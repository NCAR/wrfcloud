"""
The WrfJob class is the data model used to represent a user and associated functions
"""

import copy
import base64
import pkgutil
from typing import Union
from datetime import datetime
from wrfcloud.log import Logger
import wrfcloud.system


class WrfJob:
    """
    WRF job data object
    """

    # list of all fields supported
    ALL_KEYS = ['job_id', 'job_name', 'configuration_name', 'cycle_time', 'forecast_length',
                'output_frequency', 'status_code', 'status_message', 'progress', 'user_email']

    # do not return these fields to the user
    SANITIZE_KEYS = []

    # Status code values
    STATUS_CODE_PENDING: int = 0
    STATUS_CODE_STARTING: int = 1
    STATUS_CODE_RUNNING: int = 2
    STATUS_CODE_FINISHED: int = 3
    STATUS_CODE_CANCELED: int = 4
    STATUS_CODE_FAILED: int = 5

    def __init__(self, data: dict = None):
        """
        Initialize the user data object
        """
        # get a logger for this object
        self.log = Logger()

        # initialize the properties
        self.job_id: Union[str, None] = None
        self.job_name: Union[str, None] = None
        self.configuration_name: Union[str, None] = None
        self.cycle_time: Union[int, None] = None
        self.forecast_length: Union[int, None] = None
        self.output_frequency: Union[int, None] = None
        self.status_code: int = self.STATUS_CODE_PENDING
        self.status_message: Union[str, None] = None
        self.progress: float = 0
        self.user_email: Union[str, None] = None
        self.notify: bool = False

        # initialize from data if provided
        if data is not None:
            self.data = data

    @property
    def data(self) -> dict:
        """
        Get the data dictionary
        :return: A dictionary with all attributes
        """
        return {
            'job_id': self.job_id,
            'job_name': self.job_name,
            'configuration_name': self.configuration_name,
            'cycle_time': self.cycle_time,
            'forecast_length': self.forecast_length,
            'output_frequency': self.output_frequency,
            'status_code': self.status_code,
            'status_message': self.status_message,
            'progress': self.progress,
            'user_email': self.user_email,
            'notify': self.notify
        }

    @data.setter
    def data(self, data: dict):
        """
        Set the full or partial set of attributes
        """
        self.job_id = None if 'job_id' not in data else data['job_id']
        self.job_name = None if 'job_name' not in data else data['job_name']
        self.configuration_name = None if 'configuration_name' not in data else data['configuration_name']
        self.cycle_time = None if 'cycle_time' not in data else data['cycle_time']
        self.forecast_length = None if 'forecast_length' not in data else data['forecast_length']
        self.output_frequency = None if 'output_frequency' not in data else data['output_frequency']
        self.status_code = None if 'status_code' not in data else data['status_code']
        self.status_message = None if 'status_message' not in data else data['status_message']
        self.progress = None if 'progress' not in data else data['progress']
        self.user_email = None if 'user_email' not in data else data['user_email']
        self.notify = False if 'notify' not in data else data['notify']

        # always store cycle time as an integer
        if isinstance(self.cycle_time, datetime):
            self.cycle_time = int(self.cycle_time.timestamp())

    @property
    def sanitized_data(self) -> Union[dict, None]:
        """
        Remove any fields that should not be passed back to the user client
        :return True if user is sanitized
        """
        # get a copy of the data dictionary
        data = copy.deepcopy(self.data)

        try:
            # remove all the fields that should not be returned to the user
            for field in self.SANITIZE_KEYS:
                if field in data:
                    data.pop(field)

            # remove any extraneous keys that may have been added
            for key in data:
                if key not in self.ALL_KEYS:
                    data.pop(key)

        except Exception:
            return None
        return data

    def update(self, data: dict):
        """
        Update only the mutable fields provided in the data
        :param data: Data to update in this object
        """
        if 'job_name' in data:
            self.job_name = data['job_name']
        if 'status_code' in data:
            self.status_code = data['status_code']
        if 'status_message' in data:
            self.status_message = data['status_message']
        if 'progress' in data:
            self.progress = data['progress']
        if 'notify' in data:
            self.notify = data['notify']

    def send_complete_notification(self):
        """
        Send a complete email notification
        """
        try:
            img = base64.b64encode(pkgutil.get_data('wrfcloud', 'resources/logo.jpg')).decode()
            html = pkgutil.get_data('wrfcloud', 'resources/email_templates/job_complete.html').decode()
            html = html.replace('__APP_NAME__', wrfcloud.system.APP_NAME)
            html = html.replace('__IMAGE_DATA__', img)
            html = html.replace('__APP_URL__', wrfcloud.system.APP_URL)
            html = html.replace('__JOB_ID__', self.job_id)
            source = wrfcloud.system.SYSTEM_EMAIL_SENDER
            dest = {'ToAddresses': [self.user_email]}
            message = {
                'Subject': {
                    'Data': f'Model Run Complete {self.job_id}',
                    'Charset': 'utf-8'
                },
                'Body': {
                    'Html': {
                        'Data': html, 'Charset': 'utf-8'
                    }
                }
            }

            session = wrfcloud.system.get_aws_session()
            ses = session.client('ses')
            ses.send_email(Source=source, Destination=dest, Message=message)

            return True
        except Exception as e:
            self.log.error('Failed to send model complete email.', e)
            return False
