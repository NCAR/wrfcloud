"""
Actions related to WRF jobs
"""

from wrfcloud.api.actions.action import Action
from wrfcloud.jobs import get_all_jobs_in_system
from wrfcloud.subscribers import Subscriber, add_subscriber_to_system


class ListJobs(Action):
    """
    Get a list of all the users in the system
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # No parameters are expected or allowed
        return self.check_request_fields([], [])

    def perform_action(self) -> bool:
        """
        Put a list of all wrf jobs in the response object
        :return: True if the action ran successfully
        """
        try:
            # get all the users from the system
            jobs = get_all_jobs_in_system()

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
