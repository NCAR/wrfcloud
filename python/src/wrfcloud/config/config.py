import copy
import re
from typing import List, Union
from wrfcloud.log import Logger


class WrfConfig:
    """
    Class to contain data representing a WRF model configuration
    """
    # list of all fields supported
    ALL_KEYS: List[str] = ['name', 'description', 'wrf_namelist', 'wps_namelist', 'cores',
                           's3_key_geo_em', 's3_key_wrf_namelist', 's3_key_wps_namelist']

    # list of fields to remove from the data
    SANITIZE_KEYS: List[str] = ['s3_key_geo_em', 's3_key_wrf_namelist', 's3_key_wps_namelist']

    def __init__(self, data: dict = None):
        """
        Initialize the data values
        """
        self.log: Logger = Logger(self.__class__.__name__)
        self.name: Union[str, None] = None
        self.description: Union[str, None] = None
        self.wrf_namelist: Union[str, None] = None
        self.wps_namelist: Union[str, None] = None
        self._cores: int = 0

        if data:
            self.data = data

    @property
    def data(self) -> dict:
        """
        Get the data from this object represented as a dictionary
        :return: Data from this object represented as a dictionary
        """
        return {
            'name': self.name,
            'description': self.description,
            's3_key_geo_em': self.s3_key_geo_em,
            's3_key_wrf_namelist': self.s3_key_wrf_namelist,
            's3_key_wps_namelist': self.s3_key_wps_namelist,
            'wrf_namelist': self.wrf_namelist,
            'wps_namelist': self.wps_namelist,
            'cores': self._cores
        }

    @data.setter
    def data(self, data: dict) -> None:
        """
        Set the object's internal data values to match provided values in the dictionary
        :param data: New values for the object
        """
        self.name = data['name'] if 'name' in data else None
        self.description = data['description'] if 'description' in data else None
        self.wrf_namelist = data['wrf_namelist'] if 'wrf_namelist' in data else None
        self.wps_namelist = data['wps_namelist'] if 'wps_namelist' in data else None
        self.cores = data['cores'] if 'cores' in data else 0

    @property
    def sanitized_data(self) -> Union[dict, None]:
        """
        Remove any fields that should not be passed back to the user client
        :return: Data dictionary with some fields redacted
        """
        # get a copy of the data dictionary
        data = copy.deepcopy(self.data)

        try:
            # remove all the fields that should not be returned to the user
            for field in self.SANITIZE_KEYS:
                if field in data:
                    data.pop(field)
        except Exception as e:
            self.log.error('Failed to sanitize WRF configuration data', e)
            return None
        return data

    @property
    def s3_key_wrf_namelist(self) -> str:
        """
        Get the S3 key for the wrf namelist
        :return: S3 key
        """
        return f'configurations/{self.name}/namelist.input'

    @property
    def s3_key_wps_namelist(self) -> str:
        """
        Get the S3 key for the wps namelist
        :return: S3 key
        """
        return f'configurations/{self.name}/namelist.wps'

    @property
    def s3_key_geo_em(self) -> str:
        """
        Get the S3 key for the geo grid file
        :return: S3 key
        """
        return f'configurations/{self.name}/geo_em.d01.nc'

    @property
    def cores(self) -> int:
        """
        Get the number of compute cores
        :return: Number of compute cores to use
        """
        return self._cores

    @cores.setter
    def cores(self, core_count: int) -> None:
        """
        Set the number of cores
        :param core_count: Number of cores to use, or <= 0 to calculate number automatically
        """
        self._cores = self._calculate_optimal_core_count() if core_count <= 0 else core_count

    def validate(self) -> bool:
        """
        Validate the model configuration data
        :return: True if data are valid, otherwise False
        """
        # name must match a patter because we use it for an S3 prefix
        name_pattern = re.compile('[a-zA-Z0-9_-]+')
        match = re.fullmatch(name_pattern, self.name)
        if match is None:
            self.log.error(f'name is invalid: {self.name}')
            return False
        return True

    def _calculate_optimal_core_count(self) -> int:
        """
        Calculate the optimal number of cores to use for this configuration
        :return: Number of cores
        """
        self.log.warn('WrfConfig._calculate_optimal_core_count is not implemented.  Returning default 96 cores.')
        return 96
