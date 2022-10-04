"""
The Subscriber class is the data model used to represent a websocket client subscription
"""

import copy
from typing import Union, List


class Schedule:
    """
    Schedule data object
    """

    # list of all fields supported
    ALL_KEYS = ['ref_id', 'daily_hours', 'email', 'api_request']

    # nothing in this object should ever be sent back to the client
    SANITIZE_KEYS = []

    def __init__(self, data: dict = None):
        """
        Initialize the subscription object
        """
        # initialize the properties
        self.ref_id: Union[str, None] = None
        self.function_arn: Union[str, None] = None
        self.daily_hours: Union[List[int], None] = None
        self.email: Union[str, None] = None
        self.api_request: Union[dict, None] = None

        # initialize from data if provided
        if data is not None:
            self.data = data

    @property
    def data(self) -> dict:
        """
        Get the data dictionary
        :return: A dictionary with all attributes
        """
        return {
            'ref_id': self.ref_id,
            'function_arn': self.function_arn,
            'daily_hours': self.daily_hours,
            'email': self.email,
            'api_request': self.api_request
        }

    @data.setter
    def data(self, data: dict):
        """
        Set the full or partial set of attributes
        """
        self.ref_id = None if 'ref_id' not in data else data['ref_id']
        self.function_arn = None if 'function_arn' not in data else data['function_arn']
        self.daily_hours = None if 'daily_hours' not in data else data['daily_hours']
        self.email = None if 'email' not in data else data['email']
        self.api_request = None if 'api_request' not in data else data['api_request']

    @property
    def sanitized_data(self) -> Union[dict, None]:
        """
        Remove any fields that should not be passed back to the user client
        :return True if user is sanitized
        """
        # get a copy of the data dictionary
        data = copy.deepcopy(self.data)

        try:
            # remove all the fields that should not be returned to the user
            for field in self.SANITIZE_KEYS:
                if field in data:
                    data.pop(field)

            # remove any extraneous keys that may have been added
            for key in data:
                if key not in self.ALL_KEYS:
                    data.pop(key)

        except Exception:
            return None
        return data

    def update(self, data: dict):
        """
        Update only the mutable fields provided in the data
        :param data: Data to update in this object
        """
        if 'ref_id' in data:
            self.ref_id = data['ref_id']
        if 'function_arn' in data:
            self.function_arn = data['function_arn']
        if 'email' in data:
            self.email = data['email']
        if 'daily_hours' in data:
            self.daily_hours = data['daily_hours']
        if 'api_request' in data:
            self.api_request = data['api_request']
