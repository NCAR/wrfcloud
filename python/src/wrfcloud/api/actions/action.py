"""
The Action base class for all other actions to extend
"""

import os
from typing import List, Union
from datetime import datetime
import pkgutil
import secrets
import jwt
import yaml
from wrfcloud.log import Logger
from wrfcloud.user import User, get_user_from_system


class Action:
    """
    The base class for all API actions
    """

    # available request keys
    REQ_KEY_JWT = 'jwt'

    # available JWT keys
    JWT_KEY_EMAIL = 'email'
    JWT_KEY_ROLE = 'role'
    JWT_KEY_EXPIRES = 'expires'

    def __init__(self, run_as_user: Union[User, None] = None, request: dict = None):
        """
        Initialize the action
        :param run_as_user: Run the action as this user
        :param request: Full request message for this action
        """
        self.log = Logger(self.__class__.__name__)
        self.run_as_user = run_as_user
        self.request = request
        self.response = {}
        self.errors = []
        self.success = False
        self.additional = {}

    def run(self) -> bool:
        """
        DO NOT OVERRIDE THIS METHOD - Check permissions and execute the action
        :return: True if action ran successfully
        """
        # get the authenticated user, if any
        if self.run_as_user is None:
            self.run_as_user = self.get_user_from_request_token()

        # check for required permissions
        if not self.has_required_permissions():
            self.log.info('Insufficient permissions to execute this action.')
            self.errors.append('Insufficient permissions')
            self.additional['authorized'] = False
            return False
        self.additional['authorized'] = True

        # validate the request
        if not self.validate_request():
            self.log.info('Invalid request parameters')
            return False

        # perform the action
        self.success = self.perform_action()

        # return the success flag
        return self.success

    def get_user_from_request_token(self) -> Union[User, None]:
        """
        Attempt to get the user from the session token
        :return User matching the session token, or None
        """
        # return None if there is no session token in the request
        if Action.REQ_KEY_JWT not in self.request:
            return None

        # authenticate the JWT
        payload = self._validate_jwt(self.request[Action.REQ_KEY_JWT])

        # if JWT is not valid, return empty user
        if payload is None:
            return None

        # attempt to get a user from the JWT payload's email value
        email = payload[Action.JWT_KEY_EMAIL]
        return get_user_from_system(email)

    def has_required_permissions(self) -> bool:
        """
        Determine if the run-as user has the required role to execute this action
        :return: True if run-as user has required permissions, otherwise False
        """
        # load the role definitions
        roles = yaml.full_load(pkgutil.get_data('wrfcloud', 'api/actions/roles.yaml'))

        # set the default role to anonymous
        role_name = 'anonymous'

        # override the role name if user is authenticated
        if self.run_as_user is not None:
            role_name = self.run_as_user.get_role_id()

        # record whether the user was authenticated
        self.additional['authenticated'] = self.run_as_user is not None

        # check for unknown role value in the user
        if role_name not in roles:
            self.log.error('User is assigned to an unknown role: '
                           f'{self.run_as_user.get_email()}, {role_name}')
            return False

        # user has permissions if this class is listed in their role's permitted actions
        return self.__class__.__name__ in roles[role_name]['permitted_actions']

    def check_request_fields(self, required: List[str], allowed: List[str], data: Union[dict, None] = None) -> bool:
        """
        A function to help actions validate a request
        :param required: A list of required fields
        :param allowed: A list of accepted fields
        :param data: The data value to validate, defaults to self.request if not provided
        :return: True if all required fields are present; any non-accepted fields will be removed
        """
        # get the data value
        if data is None:
            data = self.request

        # variable to update status
        ok_required = True
        ok_allowed = True

        # make sure that all required fields are present
        for field in required:
            if field not in data:
                ok_required = False
                self.log.error(f'Request is missing required field: {field}')
        if not ok_required:
            self.errors.append('Request is missing required field.')

        # make sure the request only includes allowed fields
        allowed.append(Action.REQ_KEY_JWT)
        for field in data:
            if field not in allowed and field not in required:
                ok_allowed = False
                self.log.error(f'Request contains field that is not allowed: {field}')
        if not ok_allowed:
            self.errors.append('Request contains field that is not allowed.')

        return ok_required and ok_allowed

    def _create_jwt(self, payload: dict, expiration: int = 3600) -> str:
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
            self.log.warn('JWT_KEY is not set.  Issued JWTs will not be valid.')

        return token

    def _validate_jwt(self, token: str) -> Union[dict, None]:
        """
        Validate the token
        :param token: Token value
        :return: JWT payload IF valid, otherwise None
        """
        try:
            key = os.environ['JWT_KEY'] if 'JWT_KEY' in os.environ else secrets.token_hex(64)
            payload = jwt.decode(token, key, verify=True)
            now = datetime.utcnow().timestamp()

            if Action.JWT_KEY_EXPIRES in payload:
                if payload[Action.JWT_KEY_EXPIRES] >= now:
                    if Action.JWT_KEY_EMAIL in payload:
                        return payload
        except Exception as e:
            self.log.error('Failed to validate JWT')
            self.log.error(e)

        return None

    ##############################  ABSTRACT METHODS  ##############################

    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        self.log.error('Action is calling the abstract method: validate_request')
        self.errors.append('System error')
        return False

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        self.log.fatal('Class did not implement \'perform_action\' method: %s' %
                       self.__class__.__name__)
        return False
