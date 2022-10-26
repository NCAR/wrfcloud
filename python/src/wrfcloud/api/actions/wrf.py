"""
API actions that are responsible for reading WRF data
"""
import base64
import os
import gzip
import pkgutil
import yaml
from typing import List, Union
from datetime import datetime, timedelta
from pytz import utc
from wrfcloud.api.actions import Action
from wrfcloud.system import get_aws_session
from wrfcloud.aws.pcluster import CustomAction


class GetWrfMetaData(Action):
    """
    Get meta data for all the available WRF runs
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        required_fields = []
        return self.check_request_fields(required_fields, [])

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        try:
            # setup S3 parameters
            self.bucket: str = os.environ['WRF_OUTPUT_BUCKET']
            self.prefix: str = os.environ['WRF_OUTPUT_PREFIX']
            self.s3 = None

            # get a list of model configurations
            self.response['configurations'] = self._read_configurations()['configurations']
        except Exception as e:
            self.log.error('Failed to read model configurations.', e)
            self.errors.append('Failed to read model configurations.')
            return False

        return True

    # {
    #   configurations: [
    #     {
    #       configuration_name: 'test',
    #       cycle_times: [
    #         {
    #           cycle_time: 20220501000000,
    #           valid_times: [
    #             20220501000000,
    #             20220501010000,
    #           ]
    #         }
    #       ]
    #     }
    #   ]
    # }

    def _read_configurations(self) -> dict:
        """
        Read a list of all configurations
        :return: List of configurations
        """
        # get a list of all S3 keys in the bucket
        object_keys: List[str] = self._s3_list(self.bucket, self.prefix)

        # filter out unwanted keys
        filtered_keys = []
        for object_key in object_keys:
            if object_key.count('/') == 2:
                if '.' not in object_key.split('/')[2]:
                    filtered_keys.append(object_key)

        # create the configurations
        configs = {}
        for key in filtered_keys:
            name, cycle, valid = key.split('/')
            valid = self._parse_valid_time(valid)
            cycle = self._parse_cycle_time(cycle)
            if name not in configs:
                configs[name] = {}
            if cycle not in configs[name]:
                configs[name][cycle] = {'valid_times': []}
            if valid not in configs[name][cycle]['valid_times']:
                configs[name][cycle]['valid_times'].append(valid)

        # make the structure a bit nicer
        configs_ez_format = {'configurations': []}
        for name in configs:
            conf = {'configuration_name': name, 'cycle_times': []}
            configs_ez_format['configurations'].append(conf)
            for cycle_time in configs[name]:
                cycle = {'cycle_time': cycle_time, 'valid_times': configs[name][cycle_time]['valid_times']}
                conf['cycle_times'].append(cycle)

        return configs_ez_format

    def _s3_list(self, bucket: str, prefix: str) -> List[str]:
        """
        List objects in a bucket and prefix
        """
        # make sure we have an s3 client
        if not self.s3:
            session = get_aws_session()
            self.s3 = session.client('s3')

        # create an empty list of objects
        objects: List[str] = []

        # continuation token for listing more than 1,000 objects
        token: Union[None, str] = None
        has_more: bool = True

        # read all objects
        while has_more:
            # read up-to 1,000 objects
            response = \
                self.s3.list_objects_v2(Bucket=bucket, Prefix=prefix) if token is None else \
                self.s3.list_objects_v2(Bucket=bucket, Prefix=prefix, ContinuationToken=token)

            # process this list of objects
            if 'Contents' in response:
                for item in response['Contents']:
                    objects.append(item['Key'])

            # check if there are still more objects to retrieve
            has_more = 'NextContinuationToken' in response
            if has_more:
                token = response['NextContinuationToken']

        return objects

    @staticmethod
    def _parse_valid_time(text: str) -> int:
        """
        Parse the valid time from text
        :param text: Input text from which to parse the valid time
        :return: Valid time as milliseconds since 1970-01-01 00:00:00.000 UTC
        """
        # TODO: This parsing solution needs to be revisited after we work out the S3 data structure
        # get the string as yyyy_mm_dd_hh_mm_ss
        ymdhms: str = text[11:].replace('-', '').replace(':', '').replace('_', '')

        dt = utc.localize(datetime.strptime(ymdhms, '%Y%m%d%H%M%S'))

        return int(dt.timestamp() * 1000)

    @staticmethod
    def _parse_cycle_time(text: str) -> int:
        """
        Parse the cycle time from text
        :param text: Input text from which to parse the cycle time -- formatted as YYYYMMDDHHmmss
        :return: Cycle time as milliseconds since 1970-01-01 00:00:00.000 UTC
        """
        # TODO: This parsing solution needs to be revisited after we work out the S3 data structure
        dt = utc.localize(datetime.strptime(text, '%Y%m%d%H%M%S'))

        return int(dt.timestamp() * 1000)


class GetWrfGeoJson(Action):
    """
    Get meta data for all the available WRF runs
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        required_fields = ['configuration', 'cycle_time', 'valid_time', 'variable']
        allowed_fields = []
        return self.check_request_fields(required_fields, allowed_fields)

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        try:
            # get the S3 configuration
            self.bucket: str = os.environ['WRF_OUTPUT_BUCKET']
            self.prefix: str = os.environ['WRF_OUTPUT_PREFIX']
            self.s3 = None

            # get a geojson file
            configuration: str = self.request['configuration']
            cycle_time: int = self.request['cycle_time']
            valid_time: int = self.request['valid_time']
            variable: str = self.request['variable']
            data = self._read_geojson_data(configuration, cycle_time, valid_time, variable)
            self.response['geojson'] = base64.b64encode(data).decode()

            # put the request parameters back in the response
            self.response['configuration'] = configuration
            self.response['cycle_time'] = cycle_time
            self.response['valid_time'] = valid_time
            self.response['variable'] = variable
        except Exception as e:
            self.log.error('Failed to read model configurations.', e)
            self.errors.append('Failed to read model configurations.')
            return False

        return True

    def _read_geojson_data(self, configuration: str, cycle_time: int, valid_time: int, variable: str) -> bytes:
        """
        Read a geojson file from S3
        :param configuration: The model configuration name
        :param cycle_time: The model cycle time
        :param valid_time: The data valid time requested
        :param variable: The model variable requested
        :return: List of configurations
        """
        # build the S3 object key
        cycle_time_str = utc.localize(datetime.utcfromtimestamp(cycle_time / 1000)).strftime('%Y%m%d%H%M%S')
        valid_time_str = utc.localize(datetime.utcfromtimestamp(valid_time / 1000)).strftime('%Y-%m-%d_%H-%M-%S')
        key = f'{self.prefix}/{configuration}/{cycle_time_str}/wrfout_d01_{valid_time_str}_{variable}.geojson.gz'

        # read the object from S3
        data = self._s3_read(self.bucket, key)

        # unzip the data
        return gzip.decompress(data)

    def _s3_read(self, bucket: str, key: str) -> bytes:
        """
        List objects in a bucket and prefix
        :param bucket: Read from this S3 bucket
        :param key: Read this S3 key
        :return: Object data
        """
        # make sure we have an s3 client
        if not self.s3:
            session = get_aws_session()
            self.s3 = session.client('s3')

        # read the object
        key = key[1:] if key.startswith('/') else key
        response = self.s3.get_object(Bucket=bucket, Key=key)
        data: bytes = response['Body'].read()

        return data


class RunWrf(Action):
    """
    Run the WRF model
    """

    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        required_fields = ['configuration_name', 'start_time', 'forecast_length', 'output_frequency', 'notify']
        return self.check_request_fields(required_fields, [])

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        try:
            # create the run configuration file
            config_file = yaml.safe_load(pkgutil.get_data('wrfcloud', 'runtime/test.yml'))
            config_name = self.request['configuration_name']
            config_file['run']['local_data'] = f'/data/{self.ref_id}/gfs.t*'
            config_file['run']['workdir'] = f'/data/{self.ref_id}/{config_name}_run'
            forecast_len_sec = self.request['forecast_length']
            start_date = datetime.strptime(self.request['start_time'], '%Y-%m-%d %H:%M:%S')
            increment = timedelta(seconds=forecast_len_sec)
            end_time = start_date + increment
            config_file['run']['start'] = start_date.strftime("%Y-%m-%d_%H:%M:%S")
            config_file['run']['end'] = end_time.strftime("%Y-%m-%d_%H:%M:%S")
            config_file['run']['output_freq_sec'] = self.request['output_frequency']
            config_file['run']['configuration'] = config_name
            config_data = yaml.dump(config_file)
            config_b64_gz = base64.b64encode(gzip.compress(bytes(config_data,encoding='utf8'))).decode()

            # create the custom action to start the model
            script = f'#! /bin/bash\n' \
                     f'mkdir -p /data/{self.ref_id}\n' \
                     f'cd /data/{self.ref_id}\n' \
                     f'echo -n "{config_b64_gz}" | base64 -d | gunzip > run.yml\n' \
                     f'aws s3 sync s3://wrfcloud-xfer-tmp/ .\n' \
                     f'mkdir -p configurations/{config_name};\n' \
                     f'mv geo_em.d01.nc configurations/{config_name} \n' \
                     f'cp namelist.wps configurations/{config_name} \n' \
                     f'cp namelist.input configurations/{config_name} \n' \
                     f'unset I_MPI_OFI_PROVIDER \n' \
                     f'wrfcloud-run > log.wrfcloud-run 2>&1 & \n'
            ca = CustomAction(self.ref_id, script)

            # start the cluster
            from wrfcloud.aws.pcluster import WrfCloudCluster
            wrfcloud_cluster = WrfCloudCluster(self.ref_id)
            wrfcloud_cluster.create_cluster(ca, False)
        except Exception as e:
            self.log.error('Failed to launch WRF job', e)
            self.errors.append('Failed to launch WRF job')
            return False

        return True
