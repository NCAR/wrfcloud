"""
The JobDao class is a data access object that performs basic CRUD
(create, read, update, delete) functions on the job database.
"""

import os
import pkgutil
from typing import Union, List
import yaml
from wrfcloud.dynamodb import DynamoDao
from wrfcloud.jobs.job import WrfJob


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
        # save the item to the database
        return super().put_item(job.data)

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
        return WrfJob(data)

    def get_all_jobs(self) -> List[WrfJob]:
        """
        Get a list of all jobs in the system
        :return: List of all jobs
        """
        # Convert a list of items into a list of User objects
        return [WrfJob(item) for item in super().get_all_items()]

    def update_job(self, job: WrfJob) -> bool:
        """
        Update the job data
        :param job: Job data values to update, which must include the key field (job_id)
        :return: True if successful, otherwise False
        """
        return super().update_item(job.data)

    def delete_job(self, job: WrfJob) -> bool:
        """
        Delete the job from the database (not any associated data)
        :param job: WrfJob object
        :return: True if successful, otherwise False
        """
        job_id = job.job_id
        return super().delete_item({'job_id': job_id})

    def create_job_table(self) -> bool:
        """
        Create the job table
        :return: True if successful, otherwise False
        """
        return super().create_table(
            self.table_definition['attribute_definitions'],
            self.table_definition['key_schema']
        )
