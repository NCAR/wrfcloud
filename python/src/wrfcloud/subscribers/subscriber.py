"""
The Subscriber class is the data model used to represent a websocket client subscription
"""

import copy
from typing import Union


class Subscriber:
    """
    Subscriber data object
    """

    # list of all fields supported
    ALL_KEYS = ['client_url']

    # nothing in this object should ever be sent back to the client
    SANITIZE_KEYS = ['client_url']

    def __init__(self, data: dict = None):
        """
        Initialize the subscription object
        """
        # initialize the properties
        self.client_url: Union[str, None] = None

        # initialize from data if provided
        if data is not None:
            self.data = data

    @property
    def data(self) -> dict:
        """
        Get the data dictionary
        :return: A dictionary with all attributes
        """
        return {'client_url': self.client_url}

    @data.setter
    def data(self, data: dict):
        """
        Set the full or partial set of attributes
        """
        self.client_url = None if 'client_url' not in data else data['client_url']

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
        if 'client_url' in data:
            self.client_url = data['client_url']
