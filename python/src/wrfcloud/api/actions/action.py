"""
The Action base class for all other actions to extend
"""

from typing import List, Union
from wrfcloud.log import Logger
from wrfcloud.user import User
from wrfcloud.system import get_aws_session


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

    def __init__(self, ref_id: str, run_as_user: Union[User, None] = None, request: dict = None, client_url: str = None):
        """
        Initialize the action
        :param ref_id: Reference ID of the request
        :param run_as_user: Run the action as this user
        :param request: Full request message for this action
        :param client_url: Optional for websocket clients.  URL to send messages to client.
        """
        self.log: Logger = Logger(self.__class__.__name__)
        self.ref_id: str = ref_id
        self.run_as_user: Union[User, None] = run_as_user
        self.websocket_client_url: str = client_url
        self.request: dict = request
        self.response: dict = {}
        self.errors: List[str] = []
        self.success: bool = False
        self.additional: dict = {}
        self.client_ip: Union[str, None] = None

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
        self.log.fatal(f'Class did not implement \'perform_action\' method: {self.__class__.__name__}')
        return False

    def _s3_read(self, bucket: str, key: str) -> bytes:
        """
        Read an S3 object and return its bytes
        :param bucket: Read from this S3 bucket
        :param key: Read this S3 key
        :return: Object data
        """
        # get an s3 client
        session = get_aws_session()
        self.s3 = session.client('s3')

        # read the object
        key = key[1:] if key.startswith('/') else key
        response = self.s3.get_object(Bucket=bucket, Key=key)
        data: bytes = response['Body'].read()

        return data
