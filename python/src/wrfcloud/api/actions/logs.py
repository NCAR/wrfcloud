"""
API actions that are responsible for reading log files
"""
import os
from zipfile import ZipFile
import io

from wrfcloud.api.actions.jobs import get_job_from_system
from wrfcloud.api.actions.action import Action


class ListLogs(Action):
    """
    Get a list of all the log files for a job
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # no required parameters
        required = ['job_id']

        # optional parameters
        optional = []

        # validate the request
        return self.check_request_fields(required, optional)

    def perform_action(self) -> bool:
        """
        Put a list of all wrf jobs in the response object
        :return: True if the action ran successfully
        """
        try:
            # get the job from the system
            job = get_job_from_system(self.request['job_id'])

            # check for the job ID not found case
            if job is None:
                self.errors.append('Job ID not found.')
                self.log.error('Job ID not found: ' + self.request['job_id'])
                return False

            # get log zip file from S3
            bucket: str = os.environ['WRFCLOUD_BUCKET']
            key: str = f"jobs/{job.job_id}/logs.zip"

            # read the object from S3
            data = self._s3_read(bucket, key)

            with ZipFile(io.BytesIO(data)) as zip_file:
                self.response['log_filenames'] = zip_file.namelist()
        except Exception as e:
            self.log.error('Failed to get a list of log files for job', e)
            self.errors.append('General error')
            return False

        return True


class GetLog(Action):
    """
    Get a list of all the log files for a job
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # no required parameters
        required = ['job_id', 'log_file']

        # optional parameters
        optional = []

        # validate the request
        return self.check_request_fields(required, optional)

    def perform_action(self) -> bool:
        """
        Put a list of all wrf jobs in the response object
        :return: True if the action ran successfully
        """
        try:
            # get the job from the system
            job = get_job_from_system(self.request['job_id'])

            # check for the job ID not found case
            if job is None:
                self.errors.append(f'Job ID not found.')
                self.log.error('Job ID not found: ' + self.request['job_id'])
                return False

            # get log zip file from S3
            bucket: str = os.environ['WRFCLOUD_BUCKET']
            key: str = f"jobs/{job.job_id}/logs.zip"

            # read the object from S3
            data = self._s3_read(bucket, key)
            with ZipFile(io.BytesIO(data)) as zip_file:
                self.response['log_content'] = zip_file.read(self.request['log_file'])
        except Exception as e:
            self.log.error('Failed to get a log file content', e)
            self.errors.append('General error')
            return False

        return True
