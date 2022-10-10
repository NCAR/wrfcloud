"""
The SubscriberDao class is a data access object that performs basic CRUD
(create, read, update, delete) functions on the subscriber database.
"""

import os
import pkgutil
from typing import List
import yaml
from wrfcloud.dynamodb import DynamoDao
from wrfcloud.subscribers.subscriber import Subscriber


class SubscriberDao(DynamoDao):
    """
    CRUD operations for subscribers
    """

    def __init__(self, endpoint_url: str = None):
        """
        Create the Data Access Object (DAO)
        :param endpoint_url: (optional) Specifying the endpoint URL can be useful for testing
        """
        # load the subscriber table definition
        self.table_definition = yaml.safe_load(pkgutil.get_data('wrfcloud', 'subscribers/table.yaml'))

        # get the table name
        table_name = os.environ[self.table_definition['table_name_var']]

        # get the key fields for the table
        key_fields = self.table_definition['key_fields']

        # get the endpoint URL, but do not overwrite the local argument
        if endpoint_url is None and 'ENDPOINT_URL' in os.environ:
            endpoint_url = os.environ['ENDPOINT_URL']

        # call the super constructor
        super().__init__(table_name, key_fields, endpoint_url)

    def add_subscriber(self, subscriber: Subscriber) -> bool:
        """
        Store a new subscriber
        :param subscriber: Subscriber object to store
        :return: True if successful, otherwise False
        """
        # save the item to the database
        return super().put_item(subscriber.data)

    def get_all_subscribers(self) -> List[Subscriber]:
        """
        Get a list of all subscribers in the system
        :return: List of all subscribers
        """
        # Convert a list of items into a list of User objects
        return [Subscriber(item) for item in super().get_all_items()]

    def delete_subscriber(self, subscriber: Subscriber) -> bool:
        """
        Delete the subscriber from the database (not any associated data)
        :param subscriber: Subscriber object
        :return: True if successful, otherwise False
        """
        client_url = subscriber.client_url
        return super().delete_item({'client_url': client_url})

    def create_subscriber_table(self) -> bool:
        """
        Create the subscriber table
        :return: True if successful, otherwise False
        """
        return super().create_table(
            self.table_definition['attribute_definitions'],
            self.table_definition['key_schema']
        )
