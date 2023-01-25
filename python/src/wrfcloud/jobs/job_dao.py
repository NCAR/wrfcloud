"""
The JobDao class is a data access object that performs basic CRUD
(create, read, update, delete) functions on the job database.
"""

import os
import pkgutil
from typing import Union, List
import yaml
import base64
import hashlib
from wrfcloud.dynamodb import DynamoDao
from wrfcloud.jobs.job import WrfJob
from wrfcloud.system import get_aws_session


class JobDao(DynamoDao):
    """
    CRUD operations for jobs
    """

    def __init__(self, endpoint_url: str = None):
        """
        Create the Data Access Object (DAO)
        :param endpoint_url: (optional) Specifying the endpoint URL can be useful for testing
        """
        # load the job table definition
        self.table_definition = yaml.safe_load(pkgutil.get_data('wrfcloud', 'jobs/table.yaml'))

        # get the table name
        table_name = os.environ[self.table_definition['table_name_var']]

        # get the key fields for the table
        key_fields = self.table_definition['key_fields']

        # get the endpoint URL, but do not overwrite the local argument
        if endpoint_url is None and 'ENDPOINT_URL' in os.environ:
            endpoint_url = os.environ['ENDPOINT_URL']

        # call the super constructor
        super().__init__(table_name, key_fields, endpoint_url)

    def add_job(self, job: WrfJob) -> bool:
        """
        Store a new job
        :param job: Job object to store
        :return: True if successful, otherwise False
        """
        # clone the job because we will modify the data
        job_clone: WrfJob = WrfJob(job.data)

        # save layers to S3
        if isinstance(job_clone.layers, dict):
            ok = self._save_layers(job_clone)
            if not ok: return False

        # save the item to the database
        return super().put_item(job_clone.data)

    def get_job_by_id(self, job_id: str) -> Union[WrfJob, None]:
        """
        Get a job by job id
        :param job_id: Job ID
        :return: The job with the given job id, or None if not found
        """
        # build the database key
        key = {'job_id': job_id}

        # get the item with the key
        data = super().get_item(key)

        # handle the case where the key is not found
        if data is None:
            return None

        # build a new job object
        job: WrfJob = WrfJob(data)
        self._load_layers(job)
        return job

    def get_all_jobs(self) -> List[WrfJob]:
        """
        Get a list of all jobs in the system
        :return: List of all jobs
        """
        # Convert a list of items into a list of User objects
        jobs: List[WrfJob] = [WrfJob(item) for item in super().get_all_items()]
        for job in jobs:
            self._load_layers(job)
        return jobs

    def update_job(self, job: WrfJob) -> bool:
        """
        Update the job data
        :param job: Job data values to update, which must include the key field (job_id)
        :return: True if successful, otherwise False
        """
        # TODO: update the job data in S3, and pop the layers attribute from the data we store
        if not self._load_layers(job):
            return False

        layers: Union[str, dict] = job.data.pop('layers')
        if not isinstance(layers, dict):
            return False

        # remove or update value in layers for each data key not in key fields
        for key in [item for item in job.data if item not in self.key_fields]:
            if job.data[key] is None:
                layers.pop(key)
            else:
                layers[key] = job.data[key]

        job.data.layers = layers
        if not self._save_layers(job):
            return False

        return True
        #return super().update_item(job.data)

    def delete_job(self, job: WrfJob) -> bool:
        """
        Delete the job from the database (not any associated data)
        :param job: WrfJob object
        :return: True if successful, otherwise False
        """
        job_id = job.job_id
        ok = super().delete_item({'job_id': job_id})

        # delete the layers object from S3
        self._delete_layers(job)

        return ok

    def create_job_table(self) -> bool:
        """
        Create the job table
        :return: True if successful, otherwise False
        """
        return super().create_table(
            self.table_definition['attribute_definitions'],
            self.table_definition['key_schema']
        )

    def _save_layers(self, job: WrfJob) -> bool:
        """
        Write layers data to S3 and replace job attribute with S3 URL
        :param job: User layer data from this object
        :return: True if successful
        """
        # get the data as a dictionary
        job_data: dict = job.data

        # pop the layers dictionary out of the data dictionary and make sure it is a dictionary
        layers: Union[str, dict] = job_data.pop('layers')
        if not isinstance(layers, dict):
            return False

        # create a yaml representation of the data
        layers_yaml: bytes = yaml.dump(layers, indent=2).encode()

        # generate the S3 url -- key comes from hashing the data
        bucket_name: str = os.environ['WRFCLOUD_BUCKET_NAME']
        key: str = self._get_layers_s3key(job)
        prefix: str = 'jobs/{job.job_id}'  # TODO: find right prefixes to store next to the GeoJSON data

        # upload the data to S3
        try:
            s3 = get_aws_session().client('s3')
            s3.put_object(
                Body=layers_yaml,
                Bucket=bucket_name,
                Key=f'{prefix}/{key}'
            )
        except Exception as e:
            self.log.error('Failed to write WrfJob.layer data to S3', e)
            return False

        # set the S3 url in the job data
        job.layers = f's3://{bucket_name}/{prefix}/{key}'

        return True

    def _load_layers(self, job: WrfJob) -> bool:
        """
        Load the layers attribute from S3
        :param job: Load layers into this object
        :return: True if successful, otherwise False
        """
        # TODO:  Implement (reverse the process in _save_layers)
        # pop the layers URL out of the data dictionary and make sure it is a string
        layers: Union[str, dict] = job.data.pop('layers')

        # extract bucker name and prefix/key from S3 URL
        bucket_name, prefix_key = self._get_layers_s3bucket_and_key(layers)
        if bucket_name is None:
            return False

        # retrieve data from S3
        try:
            s3 = get_aws_session().client('s3')
            layers_yaml: bytes = s3.get_object(
                Bucket=bucket_name,
                Key=prefix_key,
            )['Body']
        except Exception as e:
            self.log.error('Failed to read WrfJob.layer data from S3', e)
            return False

        # convert YAML to Python dictionary and set job data
        job.layers = yaml.load(layers_yaml, Loader=yaml.Loader)

        return True

    def _delete_layers(self, job: WrfJob) -> bool:
        """
        Delete the layers from the S3 bucket
        :param job: Delete layers in S3 for this job
        :return: True if successful, otherwise False
        """
        # TODO: Implement
        # pop the layers URL out of the data dictionary and make sure it is a string
        layers: Union[str, dict] = job.data.pop('layers')

        # extract bucket name and prefix/key from S3 URL
        bucket_name, prefix_key = self._get_layers_s3bucket_and_key(layers)
        if bucket_name is None:
            return False

        # delete layer data from S3
        try:
            s3 = get_aws_session().client('s3')
            s3.delete_object(
                Bucket=bucket_name,
                Key=prefix_key,
            )
        except Exception as e:
            self.log.error('Failed to delete WrfJob.layer data from S3', e)
            return False

        return True

    @staticmethod
    def _get_layers_s3key(job: WrfJob) -> str:
        """
        Get the S3 key for the layers S3 object
        :param job: Get key for layers in this job
        :return: S3 key for layers of this job
        """
        # easy if the layers value is already an S3 url (i.e., a string)
        if isinstance(job.layers, str):
            return job.layers.split('/')[-1]

        # harder if to have to compute the MD5 sum of data
        layers_yaml: bytes = yaml.dump(job.layers, indent=2).encode()
        key: str = base64.b16encode(hashlib.md5(layers_yaml).digest()).decode()

        return key

    @staticmethod
    def _get_layers_s3bucket_and_key(layers_url: str) -> tuple[str, str]:
        """
        Get the S3 bucket name and key with prefix for the layers S3 object
        :param layers_url: String with S3 URl
        :return: Tuple with S3 bucket name and S3 key for layers of this job
        or (None, None) if info cannot be parsed
        """
        if not isinstance(layers_url, str):
            return None, None

        return layers_url.split('/', maxsplit=3)[2:]
