"""
The Action base class for all other actions to extend
"""

from typing import List, Union
from wrfcloud.log import Logger
from wrfcloud.user import User


class Action:
    """
    The base class for all API actions
    """

    # available request keys
    REQ_KEY_ACTION = 'action'
    REQ_KEY_JWT = 'jwt'
    REQ_KEY_REFRESH = 'refresh'
    REQ_KEY_USER = 'user'
    REQ_KEY_DATA = 'data'


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
        # validate the request
        if not self.validate_request():
            self.log.info('Invalid request parameters')
            return False

        # perform the action
        self.success = self.perform_action()

        # return the success flag
        return self.success

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
