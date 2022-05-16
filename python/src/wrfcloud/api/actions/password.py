"""
Contains Action classes related to user authentication and JWT renewal
"""
import secrets
from wrfcloud.api.actions.action import Action
from wrfcloud.user import update_user_in_system


class ChangePassword(Action):
    """
    Change a password for a user
    """

    def validate_request(self):
        """
        Validate the request
        :return: True if valid, otherwise False
        """
        required_fields = ['password0', 'password1', 'password2']
        return self.check_request_fields(required_fields, [])

    def perform_action(self):
        """
        Change own password
        :return: True if successful
        """
        # validate user
        if self.run_as_user is None:
            self.errors.append('No current user')
            return False

        # check that the new passwords match
        p1 = self.request['password1']
        p2 = self.request['password2']
        if p1 is None or p2 is None or not secrets.compare_digest(p1, p2):
            self.log.error('New passwords do not match')
            self.errors.append('New passwords do not match')
            return False

        # check the user's current password
        current_pw = self.request['password0']
        if not self.run_as_user.validate_password(current_pw):
            self.log.error('Invalid current password')
            self.errors.append('Current password is not correct')
            return False

        # set the new password and update the user
        self.run_as_user.password = p1
        updated = update_user_in_system(self.run_as_user)
        if not updated:
            self.errors.append('Error updating user values')
        return updated
