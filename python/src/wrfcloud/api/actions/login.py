"""
Contains Action classes related to user authentication and JWT renewal
"""
import secrets

import wrfcloud
from wrfcloud.api.actions.action import Action
from wrfcloud.user import User, get_user_from_system
from wrfcloud.api.auth import create_jwt
from wrfcloud.api.auth import issue_refresh_token
from wrfcloud.api.auth import get_refresh_token
from wrfcloud.api.auth import delete_refresh_token


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
                wrfcloud.api.auth.KEY_ROLE: user.role_id,
            }
            # TODO: Fix the JWT renewal in the web app, then shorten the valid time here
            self.response[Action.REQ_KEY_JWT] = create_jwt(payload, 2592000)
            self.response[Action.REQ_KEY_REFRESH] = issue_refresh_token(user)
            self.response[Action.REQ_KEY_USER] = user.sanitized_data
            return True

        # return an error response
        self.errors.append('Invalid credentials.')
        self.response = {}
        return False


class RefreshToken(Action):
    """
    Use a refresh token to issue a new JWT
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        return self.check_request_fields(['email', 'refresh_token'], [])

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        # get the full refresh token information
        token = get_refresh_token(self.request['refresh_token'])

        # make sure we found the token
        if token is None:
            self.log.error('Refresh token not found for given value')
            self.errors.append('Invalid refresh token')
            return False

        # make sure the requested email address matches the token
        if not secrets.compare_digest(token['email'], self.request['email']):
            self.log.error('SECURITY: Refresh token does not match requested user')
            self.errors.append('Invalid refresh token')
            return False

        # this should have already been done on the db request, but check again anyway
        if not secrets.compare_digest(token['refresh_token'], self.request['refresh_token']):
            self.log.error('Refresh token does not match -- this is a strange error')
            self.errors.append('Invalid refresh token')
            return False

        # delete the refresh token from the database so that it cannot be used again
        if not delete_refresh_token(token['refresh_token']):
            self.log.error('Failed to delete used refresh token')

        # get user data
        user = get_user_from_system(self.request['email'])

        # issue a new JWT and refresh token in the response
        payload = {
            wrfcloud.api.auth.KEY_EMAIL: user.email,
            wrfcloud.api.auth.KEY_ROLE: user.role_id
        }
        self.response[Action.REQ_KEY_JWT] = create_jwt(payload)
        self.response[Action.REQ_KEY_REFRESH] = issue_refresh_token(user)
        return True
