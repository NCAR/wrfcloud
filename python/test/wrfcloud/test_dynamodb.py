import boto3
from wrfcloud.dynamodb import DynamoDao


# constants to define the dynamodb table for this test
TABLE = 'ncaraws_unit_test'
KEY_FIELDS = ['id']
ENDPOINT_URL = 'http://localhost:8000'
ATTRIBUTE_DEFINITIONS = [{'AttributeName': 'id', 'AttributeType': 'S'}]
KEY_SCHEMA = [{'AttributeName': 'id', 'KeyType': 'HASH'}]


def test_create_and_read_item() -> None:
    """
    Test the operations to create and read an item
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # create sample data in item
    item = {'id': 'dynamo1', 'my_value': 11}

    # create DAO and add the item to the database
    dao = DynamoDao(TABLE, KEY_FIELDS, ENDPOINT_URL)
    assert dao.put_item(item)

    # retrieve the item from the table
    item_ = dao.get_item({'id': 'dynamo1'})

    # compare the original and retrieve items
    for key in item:
        assert key in item_
        assert item[key] == item_[key]

    # teardown the test resources
    assert _test_teardown()


def test_update_and_read_item() -> None:
    """
    Test the operations to update and read an item
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # create sample data in item
    item = {'id': 'dynamo1', 'my_value': 11}

    # create DAO and add the item to the database
    dao = DynamoDao(TABLE, KEY_FIELDS, ENDPOINT_URL)
    assert dao.put_item(item)

    # update the item in the table
    item['my_value'] = 15
    assert dao.update_item(item)

    # retrieve the item from the table and check the new expected value
    item_ = dao.get_item({'id': 'dynamo1'})
    assert item_['my_value'] == 15

    # teardown the test resources
    assert _test_teardown()


def test_create_and_delete_item() -> None:
    """
    Test the operations to create and delete an item
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # create sample data in item
    item = {'id': 'dynamo1', 'my_value': 11}

    # create DAO and add the item to the database
    dao = DynamoDao(TABLE, KEY_FIELDS, ENDPOINT_URL)
    assert dao.put_item(item)

    # retrieve the item from the table
    item_ = dao.get_item({'id': 'dynamo1'})
    assert item_ is not None

    # delete the item from the table
    dao.delete_item(item)

    # retrieve the item from the table (expected to be missing)
    item_ = dao.get_item({'id': 'dynamo1'})
    assert item_ is None

    # teardown the test resources
    assert _test_teardown()


def test_create_and_get_all_items() -> None:
    """
    Test the operations to create and delete an item
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # create dao
    dao = DynamoDao(TABLE, KEY_FIELDS, ENDPOINT_URL)

    # get all items (none expected)
    items = dao.get_all_items()
    assert not items

    # create sample data
    for n in range(50):
        item = {'id': f'dynamo{n}', 'my_value': n*n}
        assert dao.put_item(item)

    # retrieve all items from the table
    items = dao.get_all_items()
    assert len(items) == 50

    # teardown the test resources
    assert _test_teardown()


def test_create_complex_item() -> None:
    """
    Test the operations to create a complex item
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # create dao
    dao = DynamoDao(TABLE, KEY_FIELDS, ENDPOINT_URL)

    # create complex item
    item = {
        'id': 'dynamo2',
        'my_value': 56,
        'flags': [True, False, False, True],
        'string_set': ['WRF', 'MPAS', 'FV3'],
        'number_set': [22, 443, 576],
        'mixed_set': [True, 'MPAS', 576],
        'new_map': {
            'variables': ['U10', 'V10', 'T2', 'Q'],
            'compilers': ['Intel oneAPI', 'GNU'],
            'lucky_numbers': ['sqrt(-1)', 8, 3.141592654]
        }
    }

    # put the item into the table
    assert dao.put_item(item)

    # get the item from the table
    item2_ = dao.get_item({'id': 'dynamo2'})
    assert item2_ is not None
    assert item2_['new_map']['lucky_numbers'][1] == 8

    # teardown the test resources
    assert _test_teardown()


def _test_setup() -> bool:
    """
    Setup required test resources (i.e. DynamoDB table in local dynamodb)
    :return: True if successful, otherwise False
    """
    dao = DynamoDao(TABLE, KEY_FIELDS, 'http://localhost:8000')

    try:
        # just in case the table already exists, get rid of it
        dao.delete_table(TABLE)
    except Exception:
        pass

    try:
        # create the table
        return dao.create_table(ATTRIBUTE_DEFINITIONS, KEY_SCHEMA)
    except Exception as e:
        print(e)
        return False


def _test_teardown() -> bool:
    """
    Delete resources created by the tests
    :return: True if successful, otherwise False
    """
    try:
        # get a dynamodb client pointing to local dynamodb
        client = boto3.client('dynamodb', endpoint_url=ENDPOINT_URL)

        # delete the table
        client.delete_table(TableName=TABLE)
    except Exception as e:
        print(e)
        return False

    return True
