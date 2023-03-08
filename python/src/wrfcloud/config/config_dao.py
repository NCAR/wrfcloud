"""
The configDao class is a data access object that performs basic CRUD
(create, read, update, delete) functions on the config database.
"""

import io
import os
import pkgutil
from typing import Union, List
from concurrent.futures import Future, ThreadPoolExecutor
import yaml
from wrfcloud.dynamodb import DynamoDao
from wrfcloud.config import WrfConfig
from wrfcloud.system import get_aws_session


class ConfigDao(DynamoDao):
    """
    CRUD operations for configs
    """

    def __init__(self, endpoint_url: str = None):
        """
        Create the Data Access Object (DAO)
        :param endpoint_url: (optional) Specifying the endpoint URL can be useful for testing
        """
        # load the config table definition
        self.table_definition = yaml.safe_load(pkgutil.get_data('wrfcloud', 'config/table.yaml'))

        # get the table name
        table_name = os.environ[self.table_definition['table_name_var']]

        # get the key fields for the table
        key_fields = self.table_definition['key_fields']

        # get the endpoint URL, but do not overwrite the local argument
        if endpoint_url is None and 'ENDPOINT_URL' in os.environ:
            endpoint_url = os.environ['ENDPOINT_URL']

        # call the super constructor
        super().__init__(table_name, key_fields, endpoint_url)

    def add_config(self, config: WrfConfig) -> bool:
        """
        Store a new config
        :param config: config object to store
        :return: True if successful, otherwise False
        """
        # track the success state
        ok = True

        # deep copy the configuration data
        config_data = config.data

        # save the namelists to S3
        if 'wrf_namelist' in config_data:
            wrf_namelist: str = config_data.pop('wrf_namelist')
            ok = ok and self._save_namelist(config.s3_key_wrf_namelist, wrf_namelist)
        if 'wps_namelist' in config_data:
            wps_namelist: str = config_data.pop('wps_namelist')
            ok = ok and self._save_namelist(config.s3_key_wps_namelist, wps_namelist)

        # save the item to the database
        return ok and super().put_item(config_data)

    def get_config_by_name(self, name: str) -> Union[WrfConfig, None]:
        """
        Get a config by config id
        :param name: config name
        :return: The config with the given name, or None if not found
        """
        # build the database key
        key = {'name': name}

        # get the item with the key
        data = super().get_item(key)

        # handle the case where the key is not found
        if data is None:
            return None

        # build a new config object
        config = WrfConfig(data)

        # load the namelists from S3
        self._load_namelist(config, config.s3_key_wrf_namelist)
        self._load_namelist(config, config.s3_key_wps_namelist)

        return config

    def get_all_configs(self) -> List[WrfConfig]:
        """
        Get a list of all configs in the system
        :return: List of all configs
        """
        # Convert a list of items into a list of User objects
        configs: List[WrfConfig] = [WrfConfig(item) for item in super().get_all_items()]

        # Load namelists from S3
        tpe = ThreadPoolExecutor(max_workers=16)
        futures: List[Future] = [tpe.submit(self._load_namelist, config, config.s3_key_wrf_namelist) for config in configs]
        futures += [tpe.submit(self._load_namelist, config, config.s3_key_wps_namelist) for config in configs]
        for future in futures:
            future.result()

        return configs

    def update_config(self, config: WrfConfig) -> bool:
        """
        Update the config data
        :param config: config data values to update, which must include the key field (config_id)
        :return: True if successful, otherwise False
        """
        # track the success state
        ok = True

        # deep copy the configuration data
        config_data = config.data

        # save the namelists to S3
        if 'wrf_namelist' in config_data:
            wrf_namelist: str = config_data.pop('wrf_namelist')
            ok = ok and self._save_namelist(config.s3_key_wrf_namelist, wrf_namelist)
        if 'wps_namelist' in config_data:
            wps_namelist: str = config_data.pop('wps_namelist')
            ok = ok and self._save_namelist(config.s3_key_wps_namelist, wps_namelist)

        # save the item to the database
        return ok and super().update_item(config_data)

    def delete_config(self, config: WrfConfig) -> bool:
        """
        Delete the config from the database (not any associated data)
        :param config: WrfConfig object
        :return: True if successful, otherwise False
        """
        # delete the s3 objects
        ok = self._delete_namelist(config.s3_key_wrf_namelist)
        ok = ok and self._delete_namelist(config.s3_key_wps_namelist)

        # delete the dynamodb item
        return ok and super().delete_item({'name': config.name})

    def create_config_table(self) -> bool:
        """
        Create the config table
        :return: True if successful, otherwise False
        """
        return super().create_table(
            self.table_definition['attribute_definitions'],
            self.table_definition['key_schema']
        )

    def _save_namelist(self, namelist_key: str, namelist_data: str) -> bool:
        """
        Save the namelist to S3
        :param namelist_key: S3 key for the namelist
        :param namelist_data: Contents of the namelist file
        :return: True if successfully saved to S3, otherwise False
        """
        data = io.BytesIO(namelist_data.encode())
        bucket = os.environ['WRFCLOUD_BUCKET']

        try:
            s3 = get_aws_session().client('s3')
            s3.upload_fileobj(data, bucket, namelist_key)
        except Exception as e:
            self.log.error('Failed to write namelist to S3.', e)
            return False

        return True

    def _load_namelist(self, config: WrfConfig, namelist_key: str) -> bool:
        """
        Load the namelist from S3
        :param config: WRF configuration object
        :param namelist_key: S3 key of the namelist to load
        :return: True if successfully loaded, otherwise False
        """
        # get the bucket name from the environment
        bucket = os.environ['WRFCLOUD_BUCKET']

        # load the namelist into the config data
        try:
            s3 = get_aws_session().client('s3')
            data: str = s3.get_object(Bucket=bucket, Key=namelist_key)['Body'].read().decode()
            if namelist_key.endswith('namelist.input'):
                config.wrf_namelist = data
            elif namelist_key.endswith('namelist.wps'):
                config.wps_namelist = data
        except Exception as e:
            self.log.error(f'Failed to read namelist from S3. s3://{bucket}/{namelist_key}', e)
            return False

    def _delete_namelist(self, namelist_key: str) -> bool:
        """
        Delete the namelist from S3
        :param namelist_key: S3 key for the namelist
        :return: True if successful, otherwise False
        """
        bucket = os.environ['WRFCLOUD_BUCKET']

        try:
            s3 = get_aws_session().client('s3')
            s3.delete_object(Bucket=bucket, Key=namelist_key)
        except Exception as e:
            self.log.error('Failed to delete namelist from S3.', e)
            return False

        return True
