import os
import secrets
import json
from wrfcloud.user import User
from wrfcloud.user import UserDao
from wrfcloud.system import init_environment
from wrfcloud.api.handler import lambda_handler
from wrfcloud.api.handler import validate_jwt
from wrfcloud.api.actions import Action, create_jwt


init_environment(env='test')
os.environ['JWT_KEY'] = secrets.token_hex(64)


def test_lambda_handler_valid_request() -> None:
    """
    Test the lambda handler function
    :return: None
    """
    # set up the test
    _test_setup()

    # create a login request
    user = _get_sample_admin_user()
    login_request = {
        'action': 'Login',
        'data': {
            'email': user.get_email(),
            'password': '1000$moustacheCOMB'
        }
    }
    event = {
        'body': json.dumps(login_request),
        'requestContext': {
            'identity': {
                'sourceIp': '10.0.0.151'
            }
        }
    }
    response = lambda_handler(event, None)
    login_response = json.loads(response['body'])

    assert login_response['ok']
    payload = validate_jwt(login_response['data']['jwt'])
    assert payload is not None
    assert payload[Action.JWT_KEY_EMAIL] == user.get_email()

    # teardown the test
    _test_teardown()


def test_lambda_handler_insufficient_permissions() -> None:
    """
    Test the lambda handler with a user with insufficient permissions to run the request
    :return: None
    """
    # set up the test
    _test_setup()

    # create a login request
    user = _get_sample_admin_user()
    chpass_request = {
        'action': 'ChangePassword',
        'data': {
            'password0': '1000$moustacheCOMB',
            'password1': 'newpassword',
            'password2': 'newpassword'
        }
    }
    event = {
        'body': json.dumps(chpass_request),
        'requestContext': {
            'identity': {
                'sourceIp': '10.0.0.151'
            }
        }
    }
    response = lambda_handler(event, None)
    chpass_response = json.loads(response['body'])

    assert not chpass_response['ok']
    assert 'This action is unauthorized' in chpass_response['errors']

    # teardown the test
    _test_teardown()


def test_lambda_handler_action_failed() -> None:
    """
    Test the lambda handler with a user with insufficient permissions to run the request
    :return: None
    """
    # set up the test
    _test_setup()

    # create a login request
    user = _get_sample_admin_user()
    jwt = create_jwt({
        'email': user.get_email(),
        'role': user.get_role_id()
    })
    chpass_request = {
        'action': 'ChangePassword',
        'jwt': jwt,
        'data': {
            'password0': '2000$moustacheCOMB',
            'password1': 'newpassword',
            'password2': 'newpassword'
        }
    }
    event = {
        'body': json.dumps(chpass_request),
        'requestContext': {
            'identity': {
                'sourceIp': '10.0.0.151'
            }
        }
    }
    response = lambda_handler(event, None)
    chpass_response = json.loads(response['body'])

    assert not chpass_response['ok']
    assert 'Current password is not correct' in chpass_response['errors']

    # teardown the test
    _test_teardown()


def test_lambda_handler_expired_token() -> None:
    """
    Test the lambda handler function
    :return: None
    """
    # set up the test
    _test_setup()

    # create a login request
    user = _get_sample_admin_user()
    jwt = create_jwt({
        'email': user.get_email(),
        'role': user.get_role_id()
    }, -1)
    chpass_request = {
        'action': 'ChangePassword',
        'jwt': jwt,
        'data': {
            'password0': '2000$moustacheCOMB',
            'password1': 'newpassword',
            'password2': 'newpassword'
        }
    }
    event = {
        'body': json.dumps(chpass_request),
        'requestContext': {
            'identity': {
                'sourceIp': '10.0.0.151'
            }
        }
    }
    response = lambda_handler(event, None)
    chpass_response = json.loads(response['body'])

    assert not chpass_response['ok']
    assert 'Please log in first' in chpass_response['errors']

    # teardown the test
    _test_teardown()


def test_lambda_handler_unknown_role() -> None:
    """
    Test the lambda handler function
    :return: None
    """
    # set up the test
    _test_setup()

    # update the user's role to something unexpected
    user = _get_sample_admin_user()
    user.set_role_id('doubleadmin')
    assert UserDao().update_user(user)

    # create a login request
    jwt = create_jwt({
        'email': user.get_email(),
        'role': user.get_role_id()
    })
    chpass_request = {
        'action': 'ChangePassword',
        'jwt': jwt,
        'data': {
            'password0': '1000$moustacheCOMB',
            'password1': 'newpassword',
            'password2': 'newpassword'
        }
    }
    event = {
        'body': json.dumps(chpass_request),
        'requestContext': {
            'identity': {
                'sourceIp': '10.0.0.151'
            }
        }
    }
    response = lambda_handler(event, None)
    chpass_response = json.loads(response['body'])

    assert not chpass_response['ok']
    assert 'This action is unauthorized' in chpass_response['errors']

    # teardown the test
    _test_teardown()


def _test_setup() -> bool:
    """
    Setup required test resources (i.e. DynamoDB table in local dynamodb)
    :return: True if successful, otherwise False
    """
    try:
        # get a data access object
        dao = UserDao()

        try:
            # just in case the table already exists, get rid of it
            dao.delete_table(dao.table)
        except Exception:
            pass

        # create the table
        if dao.create_user_table():
            return dao.add_user(_get_sample_admin_user())
        return False
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
        dao = UserDao()
        dao.delete_table(dao.table)
    except Exception as e:
        print(e)
        return False

    return True


def _get_sample_admin_user() -> User:
    """
    Get a sample user with an admin role
    """
    # create sample user
    passwd = '1000$moustacheCOMB'
    user = User()
    user.set_name('David Hahn')
    user.set_email('hahnd+wrfcloudtest@ucar.edu')
    user.set_password(passwd)
    user.set_role_id('admin')
    user.set_active(False)
    user.set_activation_key(secrets.token_urlsafe(33))

    # make sure the password was hashed
    assert user.data[User.KEY_PASSWORD] != passwd

    return user
