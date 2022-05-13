"""
Contains Action classes related to user authentication and JWT renewal
"""
import wrfcloud
from wrfcloud.api.actions.action import Action
from wrfcloud.user import User, get_user_from_system
from wrfcloud.api.auth import create_jwt


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
                wrfcloud.api.auth.KEY_EMAIL: user.email,
                wrfcloud.api.auth.KEY_ROLE: user.role_id
            }
            self.response[Action.REQ_KEY_JWT] = create_jwt(payload)
            return True

        # return an error response
        self.errors.append('Invalid credentials.')
        self.response = {}
        return False
