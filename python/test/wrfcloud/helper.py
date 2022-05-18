from typing import List
from wrfcloud.api.audit import AuditDao
from wrfcloud.user import UserDao, User
import yaml


def _test_setup() -> bool:
    """
    Setup required test resources (i.e. DynamoDB table in local dynamodb)
    :return: True if successful, otherwise False
    """
    try:
        # get a data access object
        user_dao = UserDao()
        audit_dao = AuditDao()

        try:
            # just in case the table already exists, get rid of it
            user_dao.delete_table(user_dao.table)
            audit_dao.delete_table(audit_dao.table)
        except Exception:
            pass

        # create the table
        return user_dao.create_user_table() and audit_dao.create_audit_table()
    except Exception as e:
        print(e)
        return False


def _test_teardown() -> bool:
    """
    Delete resources created by the tests
    :return: True if successful, otherwise False
    """
    try:
        # delete the table
        user_dao = UserDao()
        audit_dao = AuditDao()
        user_dao.delete_table(user_dao.table)
        audit_dao.delete_table(audit_dao.table)
    except Exception as e:
        print(e)
        return False

    return True


def _get_sample_user(role_id: str) -> (User, str):
    """
    Get a sample user with an admin role
    :return: A sample user and its plain text password
    """
    # load sample users
    sample_users = yaml.load(open('resources/sample_users.yaml'))

    # get the first admin entry
    admin_data = sample_users['users'][role_id][0]
    admin = User(admin_data)

    # make sure the password was hashed
    assert admin.password != admin_data['password']

    # return the sample admin user
    return admin, admin_data['password']


def _get_all_sample_users() -> List[User]:
    """
    Get a sample user with an admin role
    :return: A sample user and its plain text password
    """
    # load sample users
    sample_users = yaml.load(open('resources/sample_users.yaml'))

    # get the first admin entry
    users = []
    for role in sample_users['users']:
        for user_data in sample_users['users'][role]:
            user = User(user_data)
            assert user.password != user_data['password']
            users.append(user)

    # return the sample users
    return users
