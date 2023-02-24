"""
Actions related to WRF jobs
"""

from typing import List
from wrfcloud.api.actions.action import Action
from wrfcloud.jobs import WrfJob
from wrfcloud.jobs import get_all_jobs_in_system
from wrfcloud.jobs import get_job_from_system
from wrfcloud.jobs import update_job_in_system
from wrfcloud.jobs import delete_job_from_system
from wrfcloud.jobs import WrfLayer
from wrfcloud.subscribers import Subscriber, add_subscriber_to_system
from wrfcloud.aws.pcluster import WrfCloudCluster


class ListJobs(Action):
    """
    Get a list of all the users in the system
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # no required parameters
        required = []

        # optional parameters
        optional = ['job_id']

        # validate the request
        return self.check_request_fields(required, optional)

    def perform_action(self) -> bool:
        """
        Put a list of all wrf jobs in the response object
        :return: True if the action ran successfully
        """
        try:
            # get the job(s) from the system
            jobs = get_all_jobs_in_system(full_load=False) if 'job_id' not in self.request \
                else [get_job_from_system(self.request['job_id'])]

            # check for the job ID not found case
            if 'job_id' in self.request and None in jobs:
                self.errors.append(f'Job ID not found.')
                self.log.error('Job ID not found: ' + self.request['job_id'])
                return False

            # put the sanitized user data into the response
            self.response['jobs'] = [job.sanitized_data for job in jobs]
        except Exception as e:
            self.log.error('Failed to get a list of users in the system', e)
            self.errors.append('General error')
            return False

        return True


class SubscribeJobs(Action):
    """
    Subscribe this client to job status updates -- used by websocket clients only
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # check that we have a client URL
        ok = self.websocket_client_url is not None
        if not ok:
            self.errors.append('Could not find client URL.')
            self.errors.append('This action can only be invoked by websocket clients.')

        # No parameters are expected or allowed
        return ok and self.check_request_fields([], [])

    def perform_action(self) -> bool:
        """
        Add this client to the subscription list to receive job status updates.  Since this is a
        WEBSOCKET, no response information here will be set by the user.  Here we just record the
        client ID in the persistent storage so that any updates get sent to the client.
        :return: True if the action ran successfully.
        """
        # create a new subscriber object
        subscriber = Subscriber()
        subscriber.client_url = self.websocket_client_url

        # add this subscriber to persistent storage
        added = add_subscriber_to_system(subscriber)

        # make sure we added the subscriber to storage
        if not added:
            self.log.error(f'Failed to save subscriber information: {subscriber.client_url}')
        else:
            self.log.info(f'Added subscriber: {subscriber.client_url}')

        return added


class CancelJob(Action):
    """
    Cancel an active job
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
        Cancel the job and create a response
        :return: True if the action ran successfully
        """
        # get the job and check its status
        job_id: str = self.request['job_id']
        job: WrfJob = get_job_from_system(job_id)
        if job.status_code not in [job.STATUS_CODE_PENDING, job.STATUS_CODE_STARTING, job.STATUS_CODE_RUNNING]:
            self.log.error(f'The job is not active and cannot be canceled: {job_id}')
            self.errors.append('This job is no longer active.')
            return False

        # cancel the job (i.e., shutdown the cluster)
        cluster: WrfCloudCluster = WrfCloudCluster(job.job_id)
        canceled: bool = cluster.delete_cluster(wait=False)

        # maybe add an error message for the user
        if not canceled:
            self.errors.append('Failed to cancel this job.')
            self.errors.append('Try again after refreshing job list.')

        # update the job status code
        job.status_code = job.STATUS_CODE_CANCELED
        job.status_message = f'Canceled by {self.run_as_user.full_name} ({self.run_as_user.email})'
        job.progress = 0
        update_job_in_system(job, True)

        return canceled


class DeleteJob(Action):
    """
    Delete a job (and all data) that is no longer running
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
        Delete the job and create a response
        :return: True if the action ran successfully
        """
        # get the job and check its status
        job_id: str = self.request['job_id']
        job: WrfJob = get_job_from_system(job_id)
        if job.status_code not in [job.STATUS_CODE_CANCELED, job.STATUS_CODE_FAILED, job.STATUS_CODE_FINISHED]:
            self.log.error(f'The job is still active and cannot be deleted: {job_id}')
            self.errors.append('Cancel this job before deleting.')
            return False

        # delete the data
        deleted: bool = delete_job_from_system(job)

        # maybe add an error message for the user
        if not deleted:
            self.errors.append('Failed to delete this job.')

        return deleted
