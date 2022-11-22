import os
import secrets
import json
import gzip
import base64
import wrfcloud
from wrfcloud.user import update_user_in_system
from wrfcloud.user import add_user_to_system
from wrfcloud.system import init_environment
from wrfcloud.api.handler import lambda_handler, Request
from wrfcloud.api.auth import validate_jwt
from wrfcloud.api.auth import create_jwt
from wrfcloud.api.auth import KEY_EMAIL, KEY_ROLE
from helper import _test_setup, _test_teardown, _get_sample_user


init_environment(env='test')
os.environ['JWT_KEY'] = secrets.token_hex(64)


def test_lambda_handler_valid_request() -> None:
    """
    Test the lambda handler function
    :return: None
    """
    # set up the test
    assert _test_setup()

    # create a login request
    user, plain_text = _get_sample_user('admin')
    assert add_user_to_system(user)
    login_request = {
        'action': 'Login',
        'data': {
            'email': user.email,
            'password': plain_text
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
    login_response = json.loads(gzip.decompress(base64.b64decode(response['body'])))

    assert login_response['ok']
    payload = validate_jwt(login_response['data']['jwt'])
    assert payload is not None
    assert payload[wrfcloud.api.auth.KEY_EMAIL] == user.email

    # teardown the test
    assert _test_teardown()


def test_lambda_handler_insufficient_permissions() -> None:
    """
    Test the lambda handler with a user with insufficient permissions to run the request
    :return: None
    """
    # set up the test
    assert _test_setup()
    user, plain_text = _get_sample_user('admin')

    # create a login request
    chpass_request = {
        'action': 'ChangePassword',
        'data': {
            'password0': plain_text,
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
    assert _test_teardown()


def test_lambda_handler_action_failed() -> None:
    """
    Test the lambda handler with a request that will fail
    :return: None
    """
    # set up the test
    assert _test_setup()
    user, plain_text = _get_sample_user('admin')
    assert add_user_to_system(user)

    # create a login request
    jwt = create_jwt({
        KEY_EMAIL: user.email,
        KEY_ROLE: user.role_id
    })
    chpass_request = {
        'action': 'ChangePassword',
        'jwt': jwt,
        'data': {
            'password0': 'wrong-password',
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
    chpass_response = json.loads(gzip.decompress(base64.b64decode(response['body'])))


    assert not chpass_response['ok']
    assert 'Current password is not correct' in chpass_response['errors']

    # teardown the test
    assert _test_teardown()


def test_lambda_handler_expired_token() -> None:
    """
    Test the lambda handler function
    :return: None
    """
    # set up the test
    assert _test_setup()

    # create a login request
    user, plain_text = _get_sample_user('admin')
    jwt = create_jwt({
        'email': user.email,
        'role': user.role_id
    }, -1)
    chpass_request = {
        'action': 'ChangePassword',
        'jwt': jwt,
        'data': {
            'password0': plain_text,
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
    assert _test_teardown()


def test_lambda_handler_unknown_role() -> None:
    """
    Test the lambda handler function
    :return: None
    """
    # set up the test
    assert _test_setup()
    user, plain_text = _get_sample_user('admin')
    assert add_user_to_system(user)

    # update the user's role to something unexpected
    user.role_id = 'doubleadmin'
    assert update_user_in_system(user)

    # create a login request
    jwt = create_jwt({
        KEY_EMAIL: user.email,
        KEY_ROLE: user.role_id
    })
    chpass_request = {
        'action': 'ChangePassword',
        'jwt': jwt,
        'data': {
            'password0': plain_text,
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
    assert _test_teardown()


def test_lambda_handler_eventbridge_parsing():
    """
    Test the ability to parse an event from an eventbridge source
    """
    # set up the test
    assert _test_setup()

    # create a login request
    user, plain_text = _get_sample_user('admin')
    assert add_user_to_system(user)
    jwt = create_jwt({'email': user.email, 'role': user.role_id})
    runwrf_request = {
        'action': 'RunWrf',
        'jwt': jwt,
        'data': {
            'configuration_name': 'test',
            'start_time': 1654095600,
            'forecast_length': 86400,
            'output_frequency': 3600,
            'notify': True
        }
    }

    event = {
        'source': 'aws.events',
        'request': runwrf_request
    }

    request = Request(event)
    assert not request.is_websocket
    assert request.action == 'RunWrf'
    assert 'start_time' in request.data
    assert 'forecast_length' in request.data
    assert 'output_frequency' in request.data
    assert 'notify' in request.data

    # TODO: This part of the test needs access to AWS account resources and does not run in the test environment
    # response = lambda_handler(event, None)
    # runwrf_response = json.loads(gzip.decompress(base64.b64decode(response['body'].decode())).decode())
    # assert runwrf_response['ok']
