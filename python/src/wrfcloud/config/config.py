import math
import copy
import re
from typing import List, Union
import f90nml
from wrfcloud.jobs import LatLonPoint
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
        self._domain_center: Union[LatLonPoint, None] = None
        self._domain_size_ew_meters: Union[int, None] = None
        self._domain_size_ns_meters: Union[int, None] = None
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
            'domain_center': self.domain_center.data if self.domain_center is not None else None,
            'domain_size': self.domain_size if self.domain_size is not None else None,
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
        self.domain_center = LatLonPoint(data['domain_center']) if 'domain_center' in data else None
        self.domain_size = data['domain_size'] if 'domain_size' in data else None
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

    @property
    def domain_center(self) -> LatLonPoint:
        """
        Get the domain center of this configuration
        :return: Domain center as a LatLonPoint
        """
        if not self._domain_center:
            self._compute_domain_center_and_size()
        return self._domain_center

    @domain_center.setter
    def domain_center(self, domain_center: Union[LatLonPoint, None]) -> None:
        """
        Set the domain center
        :param domain_center: The domain center
        :return: None
        """
        self._domain_center = domain_center

    @property
    def domain_size(self) -> List[int]:
        """
        Get the domain size of this configuration
        :return: Domain size in meters as an array of integers 0=east-west 1=north-south
        """
        if not self._domain_size_ew_meters or not self._domain_size_ns_meters:
            self._compute_domain_center_and_size()
        return [self._domain_size_ew_meters, self._domain_size_ns_meters]

    @domain_size.setter
    def domain_size(self, domain_size: Union[List[int], None]) -> None:
        """
        Set the domain size
        :param domain_size: Array of two integers 0=east-west 1=north-south
        :return: None
        """
        if domain_size is not None:
            self._domain_size_ew_meters = domain_size[0]
            self._domain_size_ns_meters = domain_size[1]
        else:
            self._domain_size_ew_meters = None
            self._domain_size_ns_meters = None

    def _compute_domain_center_and_size(self):
        """
        Compute the domain center and size
        """
        try:
            # parse the WPS namelist content
            wps_namelist = f90nml.reads(self.wps_namelist)
            geogrid = wps_namelist.get('geogrid')
            center_lat: float = geogrid.get('ref_lat', 0)
            center_lon: float = geogrid.get('ref_lon', 0)
            projection: str = geogrid.get('map_proj', 'mercator')
            dx: int = geogrid.get('dx', 0)
            dy: int = geogrid.get('dy', 0)
            nx: int = geogrid.get('e_we', 0)
            ny: int = geogrid.get('e_sn', 0)

            # convert degrees to meters for lat/lon projections -- does not need to be exact
            if projection == 'lat-lon':
                dx *= math.cos(center_lat*math.pi/180) * 111120
                dy *= 111120

            # calculate the horizontal domain dimensions
            meridional_distance = ny * dy
            latitudinal_distance = nx * dx

            # save the computed values
            self._domain_center = LatLonPoint({'latitude': center_lat, 'longitude': center_lon})
            self._domain_size_ew_meters = latitudinal_distance
            self._domain_size_ns_meters = meridional_distance
        except Exception as e:
            self.log.error('Failed to compute the domain center and size from namelist.wps', e)

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
