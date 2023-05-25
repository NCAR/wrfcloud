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
                logs = zip_file.namelist()

            log_dict = {}
            for log in sorted(logs):
                log = log.replace(f'data/{job.job_id}/', '')
                app, filename = log.split('/')
                if app not in log_dict:
                    log_dict[app] = []
                log_dict[app].append({'name': filename, 'full_name': f'{app}/{filename}'})

            # format logs into dictionary to display as tree in UI
            log_tree = []
            for app, filenames in log_dict.items():
                if app == 'data':
                    for filename in [item['name'] for item in filenames]:
                        log_node = {'name': filename, 'full_name': f"{app}/{filename}"}
                        log_tree.append(log_node)
                else:
                    log_node = {'name': app, 'children': filenames}
                    log_tree.append(log_node)

            self.response['log_tree'] = log_tree
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

            log_file = self.request['log_file']
            if not log_file.startswith('data/'):
                log_file = f"data/{job.job_id}/{log_file}"

            # read the object from S3
            data = self._s3_read(bucket, key)
            with ZipFile(io.BytesIO(data)) as zip_file:
                with zip_file.open(log_file) as file_handle:
                    log_content = file_handle.read()
            self.response['log_content'] = log_content.decode('utf-8')
        except Exception as e:
            self.log.error('Failed to get a log file content', e)
            self.errors.append('General error')
            return False

        return True
