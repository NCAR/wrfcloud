from typing import Union, List, Dict
import boto3
from wrfcloud.log import Logger


class DynamoDao:
    """
    Class to perform basic dynamodb operations
    """
    def __init__(self, table: str, key_fields: List[str], endpoint_url: str=None):
        """
        Create a new DynamoDao object
        :param table: dynamodb table name
        :param endpoint_url: (optional) dynamodb endpoint URL (useful for testing with local db)
        """
        self.table = table
        self.key_fields = key_fields
        self.endpoint_url = endpoint_url
        self.client = None
        self.log = Logger()

    def put_item(self, data: dict, preserve_list_order=True) -> bool:
        """
        Put a new item into a dynamodb table
        :param data: Data value to insert
        :param preserve_list_order: Use the LIST data type instead of SET to preserve order of items in list (default: True)
        :return: True if successful, otherwise False
        """
        dynamo_data = self._dict_to_dynamo(data, set_ok=(not preserve_list_order))

        client = self._get_client()
        res = client.put_item(
            TableName=self.table,
            Item=dynamo_data
        )

        return self._response_ok(res)

    def get_item(self, key: dict) -> Union[Dict, None]:
        """
        Get a dynamodb item
        :param key: Normal dictionary with key values (may include other values too)
        :return: Normal data dictionary of item if found, or None if item was not found by provided key
        """
        dynamo_key = self._make_dynamo_key(key)

        client = self._get_client()
        res = client.get_item(
            TableName=self.table,
            Key=dynamo_key
        )
        return self._dynamo_to_dict(res['Item']) if 'Item' in res else None

    def get_all_items(self, db_filter: dict = None) -> Union[List[Dict], None]:
        """
        Get all items in the dynamodb table
        :param db_filter: Optional scan filter, passed directly as ScanFilter parameter
        :return: List of zero or more dictionaries
        """
        client = self._get_client()
        res = client.scan(TableName=self.table) if db_filter is None else \
              client.scan(TableName=self.table, ScanFilter=db_filter)

        if not self._response_ok(res) or 'Items' not in res:
            return None

        return [self._dynamo_to_dict(item) for item in res['Items']]

    def update_item(self, data) -> bool:
        """
        Update an item in the dynamodb table
        :param data: Item to update, must include unmodified key
        :return: True if successful, otherwise False
        """
        update_expression = self._make_update_expression(data)
        remove_expression = self._make_remove_expression(data)

        if update_expression is None and remove_expression is None:
            return False

        client = self._get_client()
        ok = True

        if update_expression is not None:
            res = client.update_item(
                TableName=self.table,
                Key=self._make_dynamo_key(data),
                UpdateExpression=update_expression,
                ExpressionAttributeValues=self._make_expression_attribute_values(data)
            )
            ok = ok and self._response_ok(res)

        if remove_expression is not None:
            res = client.update_item(
                TableName=self.table,
                Key=self._make_dynamo_key(data),
                UpdateExpression=remove_expression
            )
            ok = ok and self._response_ok(res)

        return ok

    def delete_item(self, key: dict) -> bool:
        """
        Delete an item from the dynamodb table
        :return: True if successful, otherwise False
        """
        client = self._get_client()
        res = client.delete_item(
            TableName=self.table,
            Key=self._make_dynamo_key(key)
        )

        return self._response_ok(res)

    def create_table(self, attribute_definitions: List[Dict], key_schema: List[Dict]) -> bool:
        """
        Create a new and empty table resource
        :return: True if successful, otherwise False
        """
        try:
            # get a dynamodb client
            client = self._get_client()

            # create the table
            # TODO: We should not need to include ProvisionedThroughput here since we specify,
            #       BillingMode is PAY_PER_REQUEST, however, we get errors when not specified.
            res = client.create_table(
                TableName=self.table,
                BillingMode='PAY_PER_REQUEST',
                ProvisionedThroughput={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10},
                TableClass='STANDARD',
                AttributeDefinitions=attribute_definitions,
                KeySchema=key_schema
            )

            # check the response status
            return self._response_ok(res)
        except Exception as e:
            print(e)
            return False

    def delete_table(self, table: str) -> bool:
        """
        CAUTION: This is a destructive operation!
        Delete the table resource and all of the data contained within
        :table: Table name must match the table name referenced by this object
        :return: True if successful, otherwise False
        """
        try:
            # check that the given table name matches the referenced table
            # this merely makes it a big harder to delete something on accident
            if self.table != table:
                self.log.warn(f'Name mismatch, skipping table deletion: {self.table}')
                return False

            # get a dynamodb client pointing to local dynamodb
            client = self._get_client()

            # create the table
            res = client.delete_table(TableName=self.table)

            # return the success flag
            return self._response_ok(res)
        except Exception as e:
            print(e)
            return False














    def _make_dynamo_key(self, data: dict) -> dict:
        """
        Create a key dictionary for a dynamodb item
        :param data: Standard python dictionary to conver to a key
        :return: Crazy dynamodb key
        """
        normal_key = {}
        for key in self.key_fields:
            normal_key[key] = data[key]
        return self._dict_to_dynamo(normal_key)

    def _make_update_expression(self, data: dict) -> Union[str, None]:
        """
        Create an update expression with the dictionary
        :param data: Data dictionary to update
        :return: dynamodb update expression
        """
        update_expression = 'SET '
        for key in data:
            if key not in self.key_fields:
                if data[key] is not None:
                    update_expression += key + ' = :' + key + ', '

        if update_expression == 'SET ':
            return None

        return update_expression[:-2]

    def _make_remove_expression(self, data: dict) -> Union[str, None]:
        """
        Create an expression to remove fields
        :param data: Data dictionary look for attributes with value of None
        :return: dynamodb remove expression
        """
        remove_fields = []
        for key in data:
            if data[key] is None:
                if key not in self.key_fields:
                    remove_fields.append(key)

        if len(remove_fields) == 0:
            return None

        update_expression = 'REMOVE ' + ','.join(remove_fields)
        return update_expression

    def _make_expression_attribute_values(self, data: dict) -> dict:
        """
        Make expression update data
        :param data: Data to update
        :return: Expression update values
        """
        expression_attrs = {}
        for key in data:
            if data[key] is not None:
                if key not in self.key_fields:
                    expression_attrs[':' + key] = self._dict_to_dynamo(data[key], recursed=True)
        return expression_attrs

    def _get_client(self) -> any:
        """
        Get the dynamo client
        :return: Boto3 client for dynamo
        """
        if self.client is not None:
            return self.client

        self.client = boto3.client('dynamodb', endpoint_url=self.endpoint_url)
        return self.client

    def _dict_to_dynamo(self, data: dict, set_ok: bool=False, recursed: bool=False) -> dict:
        """
        Convert a standard python dictionary to a crazy dynamodb dictionary
        :param data: Standard python dictionary to convert
        :param set_ok: Use the SET types if possible !!SET types do not preserve order, but save a bit of space over LIST!!
        :param recursed: Caller should not specify this value.  Gets rid of 'M' on root dictionary.
        :return: Crazy dynamodb dictionary
        """
        if isinstance(data, dict):
            dynamo = {
                key: self._dict_to_dynamo(value, set_ok, True)
                for key, value in data.items()
            }
            if recursed:
                return {'M': dynamo}
            return dynamo

        if isinstance(data, list):
            if set_ok:
                if all(isinstance(e, str) for e in data):
                    return {'SS': data}
                if all(isinstance(e, (int, float)) for e in data):
                    return {'NS': [str(e) for e in data]}
                if all(isinstance(e, (bytes, bytearray)) for e in data):
                    return {'BS': [e for e in data]}
            return {'L': [self._dict_to_dynamo(value, set_ok, True) for value in data]}

        if isinstance(data, str):
            return {'S': data}
        if isinstance(data, bool):
            return {'BOOL': data}
        if isinstance(data, (int, float)):
            return {'N': str(data)}
        if isinstance(data, bytes):
            return {'B': data}
        if data is None:
            return {'NULL': True}

    def _dynamo_to_dict(self, dynamo: dict, recursed: bool=False) -> any:
        """
        Convert a crazy dynamodb dictionary to a standard python dictionary
        :param dynamo: The crazy dynamodb dictionary to convert
        :param recursed: Caller should not specify this value
        :return: The standard python dictionary
        """
        if not recursed:
            return {
                key: self._dynamo_to_dict(value, True)
                for key, value in dynamo.items()
            }

        if 'S' in dynamo:
            return dynamo['S']
        if 'N' in dynamo and '.' in dynamo['N']:
            return float(dynamo['N'])
        if 'N' in dynamo and '.' not in dynamo['N']:
            return int(dynamo['N'])
        if 'B' in dynamo:
            return dynamo['B']
        if 'BOOL' in dynamo:
            return dynamo['BOOL']
        if 'NULL' in dynamo:
            return None
        if 'SS' in dynamo:
            return dynamo['SS']
        if 'NS' in dynamo and '.' in dynamo['NS'][0]:
            return [float(e) for e in dynamo['NS']]
        if 'NS' in dynamo and '.' not in dynamo['NS'][0]:
            return [int(e) for e in dynamo['NS']]
        if 'BS' in dynamo:
            return dynamo['BS']
        if 'L' in dynamo:
            return [self._dynamo_to_dict(e, True) for e in dynamo['L']]
        if 'M' in dynamo:
            return self._dynamo_to_dict(dynamo['M'], False)

        raise RuntimeError('Missed a case converting dynamo dict to normal dict')

    @staticmethod
    def _response_ok(res: dict) -> bool:
        """
        Check if the client response is ok
        :param res: Client response
        :return: True if ok, otherwise False
        """
        return res['ResponseMetadata']['HTTPStatusCode'] == 200
