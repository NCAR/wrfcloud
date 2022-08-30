"""
Actions related to WRF jobs
"""

from wrfcloud.api.actions.action import Action
from wrfcloud.jobs import get_all_jobs_in_system


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
