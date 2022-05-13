"""
The UserDao class is a data access object that performs basic CRUD
(create, read, update, delete) functions on the user database.
"""

import os
import pkgutil
from typing import Union
import yaml
from wrfcloud.dynamodb import DynamoDao
from wrfcloud.user.user import User


class UserDao(DynamoDao):
    """
    CRUD operations for user
    """

    def __init__(self, endpoint_url: str = None):
        """
        Create the Data Access Object (DAO)
        :param endpoint_url: (optional) Specifying the endpoint URL can be useful for testing
        """
        # load the user table definition
        self.table_definition = yaml.load(pkgutil.get_data('wrfcloud', 'user/table.yaml'))

        # get the table name
        table_name = os.environ[self.table_definition['table_name_var']]

        # get the key fields for the table
        key_fields = self.table_definition['key_fields']

        # get the endpoint URL, but do not overwrite the local argument
        if endpoint_url is None and 'ENDPOINT_URL' in os.environ:
            endpoint_url = os.environ['ENDPOINT_URL']

        # call the super constructor
        super().__init__(table_name, key_fields, endpoint_url)

    def add_user(self, user: User) -> bool:
        """
        Store a new user
        :param user: User object to store
        :return: True if successful, otherwise False
        """
        # save the item to the database
        return super().put_item(user.data)

    def get_user_by_email(self, email: str) -> Union[User, None]:
        """
        Get a user by email
        :param email: User ID
        :return: The user with the given email, or None if not found
        """
        # build the database key
        key = {'email': email}

        # get the item with the key
        data = super().get_item(key)

        # handle the case where the key is not found
        if data is None:
            return None

        # build a new user object
        return User(data)

    def update_user(self, user: User) -> bool:
        """
        Update the user data
        :param user: User data values to update, which must include the key
        :return: True if successful, otherwise False
        """
        return super().update_item(user.data)

    def delete_user(self, user: User) -> bool:
        """
        Delete the user
        :param user: User object
        :return: True if successful, otherwise False
        """
        email = user.email
        return super().delete_item({'email': email})

    def create_user_table(self) -> bool:
        """
        Create the user table
        :return: True if successful, otherwise False
        """
        return super().create_table(
            self.table_definition['attribute_definitions'],
            self.table_definition['key_schema']
        )
