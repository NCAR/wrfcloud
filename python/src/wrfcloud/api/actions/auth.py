"""
Contains Action classes related to user authentication and JWT renewal
"""
import os
import jwt
import secrets
from typing import Union
from datetime import datetime
from wrfcloud.api.actions import Action
from wrfcloud.user import User, get_user_from_system, update_user_in_system
from wrfcloud.log import Logger


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
            self.response[Action.REQ_KEY_JWT] = create_jwt(payload)
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


def create_jwt(payload: dict, expiration: int = 3600) -> str:
    """
    Get a new JSON web token
    :param payload: Payload to put into the new JWT -- Payload should not include expiration
    :param expiration: Expiration time in seconds from now
    :return: Base64-encoded JWT
    """
    # add/overwrite expiration field
    payload[Action.JWT_KEY_EXPIRES] = round(datetime.utcnow().timestamp()) + expiration

    # encode the JWT
    key = os.environ['JWT_KEY'] if 'JWT_KEY' in os.environ else secrets.token_hex(64)
    token = jwt.encode(payload, key).decode()

    # maybe log a warning
    if 'JWT_KEY' not in os.environ:
        Logger().warn('JWT_KEY is not set.  Issued JWTs will not be valid.')

    return token


def validate_jwt(token: str) -> Union[dict, None]:
    """
    Validate the token
    :param token: Token value
    :return: JWT payload IF valid, otherwise None
    """
    try:
        # No token = anonymous user
        if token is None:
            return None

        key = os.environ['JWT_KEY'] if 'JWT_KEY' in os.environ else secrets.token_hex(64)
        payload = jwt.decode(token, key, verify=True)
        now = datetime.utcnow().timestamp()

        if Action.JWT_KEY_EXPIRES in payload:
            if payload[Action.JWT_KEY_EXPIRES] >= now:
                if Action.JWT_KEY_EMAIL in payload:
                    return payload
    except Exception as e:
        log = Logger()
        log.error('Failed to validate JWT')
        log.error(e)

    return None
