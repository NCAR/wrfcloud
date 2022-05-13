"""
The AuditDao class is a data access object that performs basic CRUD
(create, read, update, delete) functions on the audit log database.
"""

import os
import pkgutil
import yaml
from wrfcloud.dynamodb import DynamoDao
from wrfcloud.api.audit.entry import AuditEntry


class AuditDao(DynamoDao):
    """
    CRUD operations for audit log
    """

    def __init__(self, endpoint_url: str = None):
        """
        Create the Data Access Object (DAO)
        :param endpoint_url: (optional) Specifying the endpoint URL can be useful for testing
        """
        # load the user table definition
        self.table_definition = yaml.load(pkgutil.get_data('wrfcloud', 'api/audit/table.yaml'))

        # get the table name
        table_name = os.environ[self.table_definition['table_name_var']]

        # get the key fields for the table
        key_fields = self.table_definition['key_fields']

        # get the endpoint URL, but do not overwrite the local argument
        if endpoint_url is None and 'ENDPOINT_URL' in os.environ:
            endpoint_url = os.environ['ENDPOINT_URL']

        # call the super constructor
        super().__init__(table_name, key_fields, endpoint_url)

    def save_entry(self, entry: AuditEntry) -> bool:
        """
        Store a audit log entry
        :param entry: Audit log entry data
        :return: True if successful, otherwise False
        """
        # save the item to the database
        return super().put_item(entry.data)

    def create_audit_table(self) -> bool:
        """
        Create the user table
        :return: True if successful, otherwise False
        """
        return super().create_table(
            self.table_definition['attribute_definitions'],
            self.table_definition['key_schema']
        )
