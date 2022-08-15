"""
Classes to handle token refresh functions
"""

import os
import pkgutil
from datetime import datetime
from typing import Union
import yaml
from wrfcloud.dynamodb import DynamoDao
from wrfcloud.user import User


class RefreshTokenDao(DynamoDao):
    """
    A class to handle read/write functions on the refresh token database table
    """
    def __init__(self, endpoint_url: str = None):
        """
        Create the Data Access Object (DAO)
        :param endpoint_url: (optional) Specifying the endpoint URL can be useful for testing
        """
        # load the user table definition
        self.table_definition = yaml.safe_load(pkgutil.get_data('wrfcloud', 'api/auth/table.yaml'))

        # get the table name
        table_name = os.environ[self.table_definition['table_name_var']]

        # get the key fields for the table
        key_fields = self.table_definition['key_fields']

        # get the endpoint URL, but do not override the local argument
        if endpoint_url is None and 'ENDPOINT_URL' in os.environ:
            endpoint_url = os.environ['ENDPOINT_URL']

        # call the super constructor
        super().__init__(table_name, key_fields, endpoint_url)

    def add_refresh_token(self, user: User, token: str) -> bool:
        """
        Add a refresh token to the database for the given user
        :param user: Add the refresh token for this user
        :param token: The refresh token value
        :return: True if successful, otherwise False
        """
        # verify the length of the reset token
        if len(token) < 64:
            self.log.error(f'Refresh token length is too short: {token}')
            return False

        # add the item to the table
        return super().put_item(
            {
                'refresh_token': token,
                'exp': datetime.timestamp(datetime.utcnow()) + 7*86400,  # expire in 1 week
                'email': user.email
            }
        )

    def get_refresh_token(self, token: str, check_expiry: bool = True) -> Union[dict, None]:
        """
        Get the refresh token from the database
        :param token: The refresh token value
        :param check_expiry: If true, only return non-expired tokens
        """
        # get the full refresh token from the database
        item = super().get_item({'refresh_token': token})

        # log warning if refresh token not found
        if item is None:
            self.log.warn(f'Refresh token not found: {token}')
            return None

        # maybe check the expiry date
        if check_expiry:
            now = datetime.timestamp(datetime.utcnow())
            if item['exp'] < now:
                return None

        # return the database item
        return item

    def remove_refresh_token(self, token: str) -> bool:
        """
        Remove a refresh token from the database
        :param token: The refresh token value
        :return: True if removed, otherwise False
        """
        return super().delete_item({'refresh_token': token})

    def create_refresh_table(self) -> bool:
        """
        Create the user table
        :return: True if successful, otherwise False
        """
        return super().create_table(
            self.table_definition['attribute_definitions'],
            self.table_definition['key_schema']
        )
