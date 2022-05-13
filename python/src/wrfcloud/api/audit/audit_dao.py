"""
The AuditDao class is a data access object that performs basic CRUD
(create, read, update, delete) functions on the audit log database.
"""

import os
import pkgutil
from typing import Union, List
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

    def read_entry(self, ref_id: str) -> Union[AuditEntry, None]:
        """
        Read a log entry from the database by reference ID
        :param ref_id: The reference ID of the desired log entry
        :return: Entry if found, otherwise None
        """
        # create the log record's key
        key = {'ref_id': ref_id}

        # retrieve the item with the key
        data = super().get_item(key)

        # make sure we found an item
        if data is None:
            return None

        # build the AuditEntry object
        return AuditEntry(data)

    def get_all_entries(self) -> List[AuditEntry]:
        """
        Get all of the entries in the table
        :return: A list of all audit log entries
        """
        # get the client object
        client = self._get_client()

        # create a list to store the results
        results = []

        # make sure we get into the while loop at least once
        first = True
        last_eval_key = None

        # loop until the response does not have a LastEvaluatedKey attribute
        while first or last_eval_key:
            # query all the entries in the last 24 hours
            if first:
                res = client.scan(TableName=self.table)
            else:
                res = client.scan(TableName=self.table, ExclusiveStartKey=last_eval_key)

            # mark that we have been in the loop before
            first = False

            # check for a LastEvaluatedKey attribute, indicating there are more records to search
            last_eval_key = res['LastEvaluatedKey'] if 'LastEvaluatedKey' in res else None

            # found additional entries, add them to the results
            if self._response_ok(res) and 'Items' in res:
                # create a list of AuditEntry objects
                batch_results = [AuditEntry(self._dynamo_to_dict(item)) for item in res['Items']]

                # append this batch to the final results
                results += batch_results

        return results

    def create_audit_table(self) -> bool:
        """
        Create the user table
        :return: True if successful, otherwise False
        """
        return super().create_table(
            self.table_definition['attribute_definitions'],
            self.table_definition['key_schema']
        )
