"""
The WrfJob class is the data model used to represent a user and associated functions
"""

import os
import copy
import base64
import pkgutil
from typing import Union, List
from datetime import datetime
import pytz
from wrfcloud.log import Logger
import wrfcloud.system


class WrfJob:
    """
    WRF job data object
    """

    # list of all fields supported
    ALL_KEYS = ['job_id', 'job_name', 'configuration_name', 'forecast_length', 'output_frequency',
                'input_frequency', 'status_code', 'status_message', 'progress', 'user_email',
                'layers', 'domain_center', 'domain_size', 'start_date', 'end_date', 'cores']

    # do not return these fields to the user
    SANITIZE_KEYS = ['input_frequency']

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
        self.log = Logger(self.__class__.__name__)

        # initialize the properties
        self.job_id: Union[str, None] = None
        self.job_name: Union[str, None] = None
        self.configuration_name: Union[str, None] = None
        self.forecast_length: Union[int, None] = None
        self.output_frequency: Union[int, None] = None
        self.input_frequency: Union[int, None] = None
        self.status_code: int = self.STATUS_CODE_PENDING
        self.status_message: Union[str, None] = None
        self.progress: float = 0
        self.user_email: Union[str, None] = None
        self.notify: bool = False
        self.layers: Union[str, List[WrfLayer]] = []
        self.domain_center: Union[LatLonPoint, None] = None
        self.domain_size: Union[List[int], None] = None
        self.start_date: Union[str, None] = None
        self.end_date: Union[str, None] = None
        self.cores: Union[int, None] = None

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
            'forecast_length': self.forecast_length,
            'input_frequency': self.input_frequency,
            'output_frequency': self.output_frequency,
            'status_code': self.status_code,
            'status_message': self.status_message,
            'progress': self.progress,
            'user_email': self.user_email,
            'notify': self.notify,
            'layers': [layer.data for layer in self.layers] if isinstance(self.layers, list) else self.layers,
            'domain_center': self.domain_center.data,
            'domain_size': self.domain_size,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'cores': self.cores
        }

    @data.setter
    def data(self, data: dict):
        """
        Set the full or partial set of attributes
        :param data: Values to set
        """
        self.job_id = None if 'job_id' not in data else data['job_id']
        self.job_name = None if 'job_name' not in data else data['job_name']
        self.configuration_name = None if 'configuration_name' not in data else data['configuration_name']
        self.forecast_length = None if 'forecast_length' not in data else data['forecast_length']
        self.output_frequency = None if 'output_frequency' not in data else data['output_frequency']
        self.input_frequency = None if 'input_frequency' not in data else data['input_frequency']
        self.status_code = None if 'status_code' not in data else data['status_code']
        self.status_message = None if 'status_message' not in data else data['status_message']
        self.progress = None if 'progress' not in data else data['progress']
        self.user_email = None if 'user_email' not in data else data['user_email']
        self.notify = False if 'notify' not in data else data['notify']
        if 'layers' not in data:
            self.layers = []
        elif isinstance(data['layers'], list):
            self.layers = [WrfLayer(layer) for layer in data['layers']]
        else:
            self.layers = data['layers']
        self.domain_center = LatLonPoint() if 'domain_center' not in data else LatLonPoint(data['domain_center'])
        self.domain_size = [0, 0] if 'domain_size' not in data else data['domain_size']
        self.start_date = None if 'start_date' not in data else data['start_date']
        self.end_date = None if 'end_date' not in data else data['end_date']
        self.cores = 0 if 'cores' not in data else data['cores']

        # always store time fields as strings
        if isinstance(self.start_date, datetime):
            self.start_date = self._datetime_to_str(self.start_date)
        if isinstance(self.end_date, datetime):
            self.end_date = self._datetime_to_str(self.end_date)

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
            extra_pop_keys = []
            for key in data:
                if key not in self.ALL_KEYS:
                    extra_pop_keys.append(key)
            for extra_pop_key in extra_pop_keys:
                data.pop(extra_pop_key)

        except Exception as e:
            self.log.error('Failed to sanitize data', e)
            return None
        return data

    @property
    def wps_code_dir(self) -> str:
        """
        Get the directory with WPS code
        """
        return os.environ.get('WPS_HOME', '/home/ec2-user/WPS')

    @property
    def wrf_code_dir(self) -> str:
        """
        Get the directory with WRF code
        """
        return os.environ.get('WRF_HOME', '/home/ec2-user/WRF')

    @property
    def upp_code_dir(self) -> str:
        """
        Get the directory with UPP code
        """
        return os.environ.get('UPP_HOME', '/home/ec2-user/UPP')

    @property
    def exists(self) -> str:
        """
        Get the action to perform if a working directory exists.  For example if /data/<job_id>/wrf
        already exists, we want to remove the directory and re-run WRF.
        """
        return 'remove'

    @property
    def local_data(self) -> str:
        """
        Get the directory containing GFS data, or empty string to force download
        """
        return ''

    @property
    def work_dir(self) -> str:
        """
        Get the working directory for the job
        """
        base_dir: str = os.environ.get('WORK_DIR', '/data')
        return f'{base_dir}/{self.job_id}'

    @property
    def static_dir(self) -> str:
        """
        Get the static dir
        """
        return f'{self.work_dir}/configurations/{self.configuration_name}'

    @property
    def geogrid_dir(self):
        """
        Get the ungrib directory
        """
        return f'{self.work_dir}/geogrid'

    @property
    def ungrib_dir(self):
        """
        Get the ungrib directory
        """
        return f'{self.work_dir}/ungrib'

    @property
    def metgrid_dir(self):
        """
        Get the metgrid directory
        """
        return f'{self.work_dir}/metgrid'

    @property
    def real_dir(self):
        """
        Get the real directory
        """
        return f'{self.work_dir}/real'

    @property
    def wrf_dir(self):
        """
        Get the wrf directory
        """
        return f'{self.work_dir}/wrf'

    @property
    def derive_dir(self):
        """
        Get the derive directory
        """
        return f'{self.work_dir}/derive'

    @property
    def upp_dir(self):
        """
        Get the upp directory
        """
        return f'{self.work_dir}/upp'

    @property
    def start_year(self) -> int:
        """
        parse the start year from the start date
        :return: year as an int
        """
        return self.start_dt.year

    @property
    def start_month(self) -> int:
        """
        parse the start month from the start date
        :return: month as an int
        """
        return self.start_dt.month

    @property
    def start_day(self) -> int:
        """
        parse the start day from the start date
        :return: year as an int
        """
        return self.start_dt.day

    @property
    def start_hour(self) -> int:
        """
        parse the start hour from the start date
        :return: year as an int
        """
        return self.start_dt.hour

    @property
    def start_dt(self) -> datetime:
        """
        Get the start date/time
        :return: UTC-localized datetime
        """
        return self._str_to_datetime(self.start_date)

    @start_dt.setter
    def start_dt(self, datelike: Union[str, datetime, int, float]) -> None:
        """
        Set the start datetime from a datelike value
        :param datelike: 'yyyy-mm-dd_HH:MM:SS', datetime object, or unix timestamp as int or float
        :return None:
        """
        self.start_date = self._datelike_to_str(datelike)

    @property
    def end_year(self) -> int:
        """
        parse the end year from the end date
        :return: year as an int
        """
        return self.end_dt.year

    @property
    def end_month(self) -> int:
        """
        parse the end month from the end date
        :return: month as an int
        """
        return self.end_dt.month

    @property
    def end_day(self) -> int:
        """
        parse the end day from the end date
        :return: year as an int
        """
        return self.end_dt.day

    @property
    def end_hour(self) -> int:
        """
        parse the end hour from the end date
        :return: year as an int
        """
        return self.end_dt.hour

    @property
    def end_dt(self) -> datetime:
        """
        Get the end date/time
        :return: UTC-localized datetime
        """
        return self._str_to_datetime(self.end_date)

    @end_dt.setter
    def end_dt(self, datelike: Union[str, datetime, int, float]) -> None:
        """
        Set the end datetime from a datelike value
        :param datelike: 'yyyy-mm-dd_HH:MM:SS', datetime object, or unix timestamp as int or float
        :return None:
        """
        self.end_date = self._datelike_to_str(datelike)

    @property
    def run_hours(self) -> float:
        """
        Get the difference from start to end in hours
        :return: Forecast length in hours
        """
        end_dt: datetime = self._str_to_datetime(self.end_date)
        start_dt: datetime = self._str_to_datetime(self.start_date)

        return (end_dt.timestamp() - start_dt.timestamp()) / 3600

    @property
    def output_freq_min(self) -> float:
        """
        Get the output frequency in minutes
        :return: Output frequency in minutes
        """
        return self.output_frequency / 60

    @property
    def output_freq_sec(self) -> float:
        """
        Get the output frequency in seconds
        :return: Output frequency in seconds
        """
        return self.output_frequency

    @property
    def input_freq_sec(self) -> float:
        """
        Get the input frequency in seconds
        :return: Input frequency in seconds
        """
        return self.input_frequency

    @staticmethod
    def _datelike_to_str(datelike: Union[str, datetime, int, float]) -> str:
        """
        Set the end datetime from a datelike value
        :param datelike: 'yyyy-mm-dd_HH:MM:SS', datetime object, or unix timestamp as int or float
        :return: UTC string in the format 'yyyy-mm-dd_HH:MM:SS'
        """
        if isinstance(datelike, str):
            return datelike
        if isinstance(datelike, datetime):
            return WrfJob._datetime_to_str(datelike)
        if isinstance(datelike, int) or isinstance(datelike, float):
            return WrfJob._datetime_to_str(pytz.utc.localize(datetime.utcfromtimestamp(datelike)))

    @staticmethod
    def _str_to_datetime(date: str) -> datetime:
        """
        Convert a UTC date string to a datetime object
        :param date: UTC date in the format YYYY-mm-dd_HH:MM:SS
        :return: datetime object representing the string value
        """
        date_format: str = '%Y-%m-%d_%H:%M:%S'
        return pytz.utc.localize(datetime.strptime(date, date_format))

    @staticmethod
    def _datetime_to_str(date: datetime) -> str:
        """
        Convert a UTC datetime object to a string
        :param date: datetime object
        :return: UTC date in the format YYYY-mm-dd_HH:MM:SS
        """
        date_format: str = '%Y-%m-%d_%H:%M:%S'
        return date.strftime(date_format)

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
        if 'configuration_name' in data:
            self.configuration_name = data['configuration_name']
        if 'forecast_length' in data:
            self.forecast_length = data['forecast_length']
        if 'output_frequency' in data:
            self.output_frequency = data['output_frequency']
        if 'input_frequency' in data:
            self.input_frequency = data['input_frequency']
        if 'user_email' in data:
            self.user_email = data['user_email']
        if 'layers' in data:
            self.layers = [WrfLayer(layer) for layer in data['layers']]
        if 'domain_center' in data:
            self.domain_center = LatLonPoint(data['domain_center'])
        if 'domain_size' in data:
            self.domain_size = data['domain_size']
        if 'start_date' in data:
            self.start_date = data['start_date']
        if 'end_date' in data:
            self.end_date = data['end_date']
        if 'cores' in data:
            self.cores = data['cores']

    def send_complete_notification(self):
        """
        Send a complete email notification
        """
        try:
            img = base64.b64encode(pkgutil.get_data('wrfcloud', 'resources/logo.jpg')).decode()
            html = pkgutil.get_data('wrfcloud', 'resources/email_templates/job_complete.html').decode()
            html = html.replace('__APP_NAME__', os.environ['APP_NAME'])
            html = html.replace('__IMAGE_DATA__', img)
            html = html.replace('__APP_URL__', os.environ['APP_HOSTNAME'])
            html = html.replace('__JOB_ID__', self.job_id)
            source = os.environ['ADMIN_EMAIL']
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


class LatLonPoint:
    """
    Latitude and longitude point object
    """
    def __init__(self, data: dict = None):
        """
        Initialize the lat/lon point
        """
        # initialize the properties
        self.latitude: float = 0
        self.longitude: float = 0

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
            'latitude': self.latitude,
            'longitude': self.longitude
        }

    @data.setter
    def data(self, data: dict):
        """
        Set the full or partial set of attributes
        :param data: Values to set
        """
        self.latitude = self.latitude if 'latitude' not in data else data['latitude']
        self.longitude = self.longitude if 'longitude' not in data else data['longitude']


class WrfLayer:
    """
    View details of a WRF layer
    """
    def __init__(self, data: dict = None):
        """
        Initialize the WRF layer object
        """
        # initialize the properties
        self.variable_name: str = ''
        self.display_name: str = ''
        self.palette: Union[Palette, None] = None
        self.units: str = ''
        self.visible: bool = False
        self.opacity: float = 1
        self.layer_data: any = None
        self.z_level: Union[int, None] = None
        self.time_step: float = 0
        self.dt: int = 0

        # initialize from data if provided
        if data is not None:
            self.data = data

    @property
    def dt_str(self) -> str:
        """
        Get the date/time formatted as yyyymmddHHMMSS
        :return: Date/time as string
        """
        return pytz.utc.localize(datetime.utcfromtimestamp(self.dt)).strftime('%Y%m%d%H%M%S')

    @property
    def data(self) -> dict:
        """
        Get the data dictionary
        :return: A dictionary with all attributes
        """
        return {
            'variable_name': self.variable_name,
            'display_name': self.display_name,
            'palette': self.palette.data if self.palette is not None else None,
            'units': self.units,
            'visible': self.visible,
            'opacity': self.opacity,
            'layer_data': self.layer_data if isinstance(self.layer_data, str) else None,
            'z_level': self.z_level,
            'time_step': self.time_step,
            'dt': self.dt,
        }

    @data.setter
    def data(self, data: dict):
        """
        Set the full or partial set of attributes
        :param data: Values to set
        """
        self.variable_name = data['variable_name'] if 'variable_name' in data else ''
        self.display_name = data['display_name'] if 'display_name' in data else ''
        self.palette = Palette(data['palette']) if 'palette' in data else None
        self.units = data['units'] if 'units' in data else ''
        self.visible = data['visible'] if 'visible' in data else False
        self.opacity = data['opacity'] if 'opacity' in data else 1
        self.layer_data = data['layer_data'] if 'layer_data' in data else None
        self.z_level = data['z_level'] if 'z_level' in data else None
        self.time_step = data['time_step'] if 'time_step' in data else 0
        self.dt = data['dt'] if 'dt' in data else 0


class Palette:
    """
    Details of a color palette
    """
    def __init__(self, data: dict = None):
        """
        Initialize the palette layer object
        """
        # initialize the properties
        self.palette_name: str = ''
        self.min_value: float = 0
        self.max_value: float = 100

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
            'palette_name': self.palette_name,
            'min_value': self.min_value,
            'max_value': self.max_value
        }

    @data.setter
    def data(self, data: dict):
        """
        Set the full or partial set of attributes
        :param data: Values to set
        """
        self.palette_name = data['palette_name'] if 'palette_name' in data else ''
        self.min_value = data['min_value'] if 'min_value' in data else 0
        self.max_value = data['max_value'] if 'max_value' in data else 100
