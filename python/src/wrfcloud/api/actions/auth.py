"""
Contains Action classes related to user authentication and JWT renewal
"""
import secrets

from wrfcloud.api.actions import Action
from wrfcloud.user import User, get_user_from_system, update_user_in_system


class Login(Action):
    """
    Login action
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        required_fields = ['email', 'password']
        return self.check_request_fields(required_fields, [])

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        # get the email and password from the request
        email = self.request['email']
        password = self.request['password']

        # try to get the user from the system
        user = get_user_from_system(email)

        # get a fake user if not authenticated -- helps to prevent timing attacks
        if user is None:
            user = User()

        # issue a JWT if the password matches
        if user.validate_password(password):
            payload = {
                Action.JWT_KEY_EMAIL: user.get_email(),
                Action.JWT_KEY_ROLE: user.get_role_id()
            }
            self.response[Action.REQ_KEY_JWT] = self._create_jwt(payload)
            return True

        # return an error response
        self.errors.append('Invalid credentials.')
        self.response = {}
        return False


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
        self.run_as_user.set_password(p1)
        updated = update_user_in_system(self.run_as_user)
        if not updated:
            self.errors.append('Error updating user values')
        return updated
