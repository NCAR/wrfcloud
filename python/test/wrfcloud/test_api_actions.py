import os
import secrets
import hashlib
import base64
from wrfcloud.api.actions import Login
from wrfcloud.api.actions import RefreshToken
from wrfcloud.api.actions import ChangePassword
from wrfcloud.api.actions import CreateUser
from wrfcloud.api.actions import ActivateUser
from wrfcloud.api.actions import ListUsers
from wrfcloud.api.actions import UpdateUser
from wrfcloud.api.actions import DeleteUser
from wrfcloud.api.actions import WhoAmI
from wrfcloud.api.actions import RequestPasswordRecoveryToken
from wrfcloud.api.actions import ResetPassword
from wrfcloud.api.actions import RunWrf
from wrfcloud.api.actions import GetWrfMetaData
from wrfcloud.api.actions import GetWrfGeoJson
from wrfcloud.api.auth import create_jwt, validate_jwt
from wrfcloud.api.auth import issue_refresh_token
from wrfcloud.api.auth import get_refresh_token
from wrfcloud.api.handler import create_reference_id
from wrfcloud.user import User
from wrfcloud.user import add_user_to_system
from wrfcloud.user import get_user_from_system
from wrfcloud.user import update_user_in_system
from wrfcloud.user import delete_user_from_system
from wrfcloud.system import init_environment
from wrfcloud.api.auth import get_user_from_jwt

from helper import _test_teardown, _test_setup, _get_sample_user, _get_all_sample_users

init_environment(env='test')
os.environ['JWT_KEY'] = secrets.token_hex(64)


def test_login() -> None:
    """
    Test the login action
    :return: None
    """
    # set up the test
    assert _test_setup()
    user, plain_text = _get_sample_user('admin')
    assert add_user_to_system(user)

    # create the request and run the action - valid login
    ref_id = create_reference_id()
    request = {'email': user.email, 'password': plain_text}
    login = Login(ref_id=ref_id, run_as_user=None, request=request)
    assert login.run()
    user_ = get_user_from_jwt(login.response['jwt'])
    assert login.REQ_KEY_REFRESH in login.response
    assert user.email == user_.email

    # create the request and run the action - wrong password
    ref_id = create_reference_id()
    request = {'email': user.email, 'password': 'wr0nGP@$Sw0RD!'}
    login = Login(ref_id=ref_id, run_as_user=None, request=request)
    assert not login.run()
    assert 'jwt' not in login.response

    # create the request and run the action - email not in system
    assert delete_user_from_system(user)
    ref_id = create_reference_id()
    request = {'email': user.email, 'password': plain_text}
    login = Login(ref_id=ref_id, run_as_user=None, request=request)
    assert not login.run()
    assert 'jwt' not in login.response

    # teardown the test
    assert _test_teardown()


def test_change_password() -> None:
    """
    Test the change password action
    :return: None
    """
    # set up the test
    assert _test_setup()
    user, plain_text = _get_sample_user('admin')
    assert add_user_to_system(user)

    # create the request and run the action - valid change password
    ref_id = create_reference_id()
    request = {
        'password0': plain_text,
        'password1': 'mys@f#newpasw#rd',
        'password2': 'mys@f#newpasw#rd'
    }
    chpass = ChangePassword(ref_id=ref_id, run_as_user=user, request=request)
    assert chpass.run()

    # check that the password was really changed
    user_ = get_user_from_system(user.email)
    assert user_.validate_password('mys@f#newpasw#rd')

    # create the request and run the action - change anonymous user password
    ref_id = create_reference_id()
    request = {
        'password0': plain_text,
        'password1': 'mys@f#newpasw#rd',
        'password2': 'mys@f#newpasw#rd'
    }
    chpass = ChangePassword(ref_id=ref_id, run_as_user=None, request=request)
    assert not chpass.run()

    # create the request and run the action - new passwords do not match
    ref_id = create_reference_id()
    request = {
        'password0': 'mys@f#newpasw#rd',
        'password1': 'fdsafdsafdsa',
        'password2': 'asdfasdfasdf'
    }
    chpass = ChangePassword(ref_id=ref_id, run_as_user=user, request=request)
    assert not chpass.run()

    # check that the password was not changed
    user_ = get_user_from_system(user.email)
    assert user_.validate_password('mys@f#newpasw#rd')

    # create the request and run the action - invalid current password
    ref_id = create_reference_id()
    request = {
        'password0': 'myWRONGpasw#rd',
        'password1': 'asdfasdfasdf',
        'password2': 'asdfasdfasdf'
    }
    chpass = ChangePassword(ref_id=ref_id, run_as_user=user, request=request)
    assert not chpass.run()

    # check that the password was not changed
    user_ = get_user_from_system(user.email)
    assert user_.validate_password('mys@f#newpasw#rd')


def test_invalid_request_parameters() -> None:
    """
    Check error handling for invalid request parameters
    :return: None
    """
    # set up the test
    assert _test_setup()
    user, plain_text = _get_sample_user('admin')
    assert add_user_to_system(user)

    # create the request and run the action - invalid request parameters
    ref_id = create_reference_id()
    request = {
        'email': user.email,
        'wrong_key': plain_text
    }
    login = Login(ref_id=ref_id, request=request)
    assert not login.run()
    assert not login.success
    assert 'jwt' not in login.response

    # teardown the test
    assert delete_user_from_system(user)
    assert _test_teardown()


def test_setup_new_user() -> None:
    """
    Test the CreateUser action
    :return: None
    """
    # set up the test
    assert _test_setup()
    admin, plain_text = _get_sample_user('admin')
    assert add_user_to_system(admin)

    # create the request to create a new user
    reg_user, user_pw = _get_sample_user('regular')
    ref_id = create_reference_id()
    request = {
        'user': {
            'full_name': reg_user.full_name,
            'email': reg_user.email,
            'role_id': reg_user.role_id
        }
    }

    # create and run the action
    action = CreateUser(ref_id=ref_id, run_as_user=admin, request=request)
    assert action.run()
    assert action.success
    assert not action.errors

    # get the new user from the database
    user = get_user_from_system(reg_user.email)
    assert user is not None
    assert not user.active
    assert user.password is None
    assert user.reset_token is None
    assert not user.validate_password('None')
    assert not user.validate_password(None)
    assert not user.validate_password('')

    # activate the user with a new action
    ref_id = create_reference_id()
    request = {
        'email': user.email,
        'activation_key': user.activation_key,
        'new_password': user_pw
    }
    action = ActivateUser(ref_id=ref_id, run_as_user=None, request=request)
    assert action.run()
    assert action.success
    assert not action.errors

    # get the updated user from the database
    user = get_user_from_system(user.email)
    assert user is not None
    assert user.active
    assert user.validate_password(user_pw)

    # run the action again -- should fail
    assert not action.run()
    assert not action.success
    assert 'Account is already active' in action.errors

    # teardown the test
    assert _test_teardown()


def test_user_with_same_email() -> None:
    """
    Try to set up a new user with the same email as another user
    """
    # set up the test case
    assert _test_setup()
    admin, plain_text = _get_sample_user('admin')
    assert add_user_to_system(admin)

    # try to create a new user with the same email address
    reg_user, _ = _get_sample_user('regular')
    ref_id = create_reference_id()
    request = {
        'user': {
            'full_name': reg_user.full_name,
            'email': admin.email,
            'role_id': reg_user.role_id
        }
    }
    action = CreateUser(ref_id=ref_id, run_as_user=admin, request=request)
    assert not action.run()
    assert not action.success
    assert 'Email address is already in use' in action.errors

    # teardown the test case
    assert _test_teardown()


def test_activate_user_twice() -> None:
    """
    Try to activate the user again with the same activation key
    """
    # set up the test case
    assert _test_setup()
    admin, plain_text = _get_sample_user('admin')
    admin.active = True
    assert add_user_to_system(admin)

    # create an activation request
    ref_id = create_reference_id()
    request = {
        'email': admin.email,
        'activation_key': admin.activation_key,
        'new_password': plain_text
    }
    action = ActivateUser(ref_id=ref_id, run_as_user=None, request=request)
    assert not action.run()
    assert not action.success
    assert 'Account is already active' in action.errors

    # teardown the test case
    assert _test_teardown()


def test_activate_user_with_weak_password() -> None:
    """
    Try to activate the user again with the same activation key
    """
    # set up the test case
    assert _test_setup()
    admin, _ = _get_sample_user('admin')
    admin.active = False
    assert not admin.active
    assert add_user_to_system(admin)

    # create an activation request
    ref_id = create_reference_id()
    request = {
        'email': admin.email,
        'activation_key': admin.activation_key,
        'new_password': 'abc123'
    }
    action = ActivateUser(ref_id=ref_id, run_as_user=None, request=request)
    assert not action.run()
    assert not action.success
    assert 'Password must be at least 10 characters long' in action.errors

    # teardown the test case
    assert _test_teardown()


def test_activate_unknown_user() -> None:
    """
    Try to activate a user not in the system
    """
    # set up test case
    assert _test_setup()

    # create an activate request
    reg_user, plain_text = _get_sample_user('regular')
    ref_id = create_reference_id()
    request = {
        'email': reg_user.email,
        'activation_key': reg_user.activation_key,
        'new_password': plain_text
    }
    action = ActivateUser(ref_id=ref_id, run_as_user=None, request=request)
    assert not action.run()
    assert not action.success
    assert 'Invalid activation key' in action.errors

    # teardown the test case
    assert _test_teardown()


def test_list_users() -> None:
    """
    Test the action to list all users in the system
    """
    # set up the test
    _test_setup()
    users = _get_all_sample_users()
    for user in users:
        assert add_user_to_system(user)

    # create a list users request
    admin, _ = _get_sample_user('regular')
    ref_id = create_reference_id()
    request = {}
    action = ListUsers(ref_id=ref_id, run_as_user=admin, request=request)
    assert action.run()
    assert action.success
    assert len(action.response['users']) == len(users)
    for user_data in action.response['users']:
        for attr in ['email', 'full_name', 'role_id']:
            assert attr in user_data
        for sani_key in User.SANITIZE_KEYS:
            assert sani_key not in user_data

    # teardown the test case
    assert _test_teardown()


def test_update_user() -> None:
    """
    Test the action to update a user in the system
    """
    # set up the test
    _test_setup()
    user, _ = _get_sample_user('regular')
    admin, _ = _get_sample_user('admin')
    assert add_user_to_system(user)
    assert add_user_to_system(admin)

    # create an update user request
    ref_id = create_reference_id()
    request = {
        'user': {
            'email': user.email,
            'full_name': 'Joe Bauers'
        }
    }
    action = UpdateUser(ref_id=ref_id, run_as_user=admin, request=request)
    assert action.run()
    assert action.success
    response_user = User(action.response['user'])
    assert response_user.email == user.email
    assert response_user.full_name == 'Joe Bauers'
    db_user = get_user_from_system(user.email)
    assert db_user.full_name == 'Joe Bauers'

    # teardown the test case
    assert _test_teardown()


def test_update_unknown_user() -> None:
    """
    Test the action to update a user in the system
    """
    # set up the test
    _test_setup()
    user, _ = _get_sample_user('regular')
    admin, _ = _get_sample_user('admin')
    assert add_user_to_system(admin)

    # create an update user request
    ref_id = create_reference_id()
    request = {
        'user': {
            'email': user.email,
            'full_name': 'Joe Bauers'
        }
    }
    action = UpdateUser(ref_id=ref_id, run_as_user=admin, request=request)
    assert not action.run()
    assert not action.success
    assert 'Unknown user' in action.errors

    # teardown the test case
    assert _test_teardown()


def test_delete_user() -> None:
    """
    Test the delete user action
    """
    # set up the test
    assert _test_setup()
    admin, _ = _get_sample_user('admin')
    user, _ = _get_sample_user('regular')
    assert add_user_to_system(admin)
    assert add_user_to_system(user)

    # create a request to delete a user
    ref_id = create_reference_id()
    request = {'email': user.email}
    action = DeleteUser(ref_id=ref_id, run_as_user=admin, request=request)
    assert action.run()
    assert action.success

    # teardown the test
    assert _test_teardown()


def test_delete_unknown_user() -> None:
    """
    Test the delete user action
    """
    # set up the test
    assert _test_setup()
    admin, _ = _get_sample_user('admin')
    user, _ = _get_sample_user('regular')
    assert add_user_to_system(admin)

    # create a request to delete a user
    ref_id = create_reference_id()
    request = {'email': user.email}
    action = DeleteUser(ref_id=ref_id, run_as_user=admin, request=request)
    assert not action.run()
    assert not action.success
    assert 'User not found' in action.errors

    # teardown the test
    assert _test_teardown()


def test_whoami() -> None:
    """
    Test the whoami action
    """
    # set up the test
    assert _test_setup()
    user, _ = _get_sample_user('regular')
    assert add_user_to_system(user)

    # create a request to get a user's own information
    ref_id = create_reference_id()
    request = {}
    action = WhoAmI(ref_id=ref_id, run_as_user=user, request=request)
    assert action.run()
    assert action.success
    assert 'user' in action.response
    assert 'active' in action.response['user']

    # teardown the test
    assert _test_teardown()


def test_password_reset() -> None:
    """
    Test the password reset process
    """
    # set up the test
    assert _test_setup()
    user, _ = _get_sample_user('regular')
    assert add_user_to_system(user)

    # create a request to add a reset token
    assert user.reset_token is None
    ref_id = create_reference_id()
    request = {'email': user.email}
    action = RequestPasswordRecoveryToken(ref_id=ref_id, run_as_user=None, request=request)
    assert action.run()
    assert action.success
    user_ = get_user_from_system(user.email)
    token_age = user_.get_seconds_since_reset_token_sent()
    assert 10 > token_age > 0
    token = user_.reset_token.split(';')[1]
    assert user_.validate_reset_token(token)

    # try to set another reset token too quickly
    action = RequestPasswordRecoveryToken(ref_id=ref_id, run_as_user=None, request=request)
    assert not action.run()
    assert not action.success
    assert 'You must wait at least 10 minutes before requesting another reset email' in action.errors

    # user the reset token to reset the password
    ref_id = create_reference_id()
    request = {
        'email': user_.email,
        'reset_token': user_.reset_token.split(';')[1],
        'new_password': '100shredsOFcabbage'
    }
    action = ResetPassword(ref_id=ref_id, run_as_user=None, request=request)
    assert action.run()
    assert action.success

    # verify the password was changed
    user_ = get_user_from_system(user_.email)
    assert user_.validate_password('100shredsOFcabbage')

    # teardown the test
    assert _test_teardown()


def test_reset_password_for_unknown_user() -> None:
    """
    Try to reset a password for an unknown user
    """
    # set up test case
    assert _test_setup()

    # create a request
    ref_id = create_reference_id()
    request = {
        'email': 'unknown@example.com',
        'reset_token': User().reset_token,
        'new_password': '100shredsOFcabbage'
    }
    action = ResetPassword(ref_id=ref_id, run_as_user=None, request=request)
    assert not action.run()
    assert not action.success
    assert 'Password reset failed' in action.errors

    # teardown test case
    assert _test_teardown()


def test_reset_password_with_invalid_token() -> None:
    """
    Try to reset a password with a wrong
    """
    # set up test case
    assert _test_setup()
    user, _ = _get_sample_user('regular')
    assert add_user_to_system(user)

    # test with no reset token set in the system user
    ref_id = create_reference_id()
    request = {
        'email': user.email,
        'reset_token': User().reset_token,
        'new_password': '100shredsOFcabbage'
    }
    action = ResetPassword(ref_id=ref_id, run_as_user=None, request=request)
    assert not action.run()
    assert not action.success
    assert 'Password reset failed' in action.errors

    # test with a valid reset token set in the system user
    user.reset_token = User().reset_token
    assert update_user_in_system(user)
    ref_id = create_reference_id()
    request = {
        'email': user.email,
        'reset_token': User().reset_token,  # get a random token value
        'new_password': '100shredsOFcabbage'
    }
    action = ResetPassword(ref_id=ref_id, run_as_user=None, request=request)
    assert not action.run()
    assert not action.success
    assert 'Password reset failed' in action.errors

    # teardown test case
    assert _test_teardown()


def test_refresh_token() -> None:
    """
    Test the action to get a new JWT with a refresh token
    """
    # set up test case
    assert _test_setup()
    user, _ = _get_sample_user('regular')
    assert add_user_to_system(user)

    # artificially inject a refresh token into the system and create a valid JWT
    jwt = create_jwt({'email': user.email, 'role_id': user.role_id})
    refresh_token = issue_refresh_token(user)

    # create a request to renew a JWT
    ref_id = create_reference_id()
    request = {
        'email': user.email,
        'refresh_token': refresh_token
    }
    action = RefreshToken(ref_id=ref_id, run_as_user=user, request=request)
    assert action.run()
    new_jwt = action.response['jwt']
    new_refresh_token = action.response[action.REQ_KEY_REFRESH]

    # make sure we have new jwt and refresh tokens
    assert new_jwt is not None
    assert new_refresh_token is not None
    assert new_jwt != jwt
    assert new_refresh_token != refresh_token
    assert validate_jwt(new_jwt)

    # make sure the old refresh token was removed
    assert get_refresh_token(refresh_token) is None
    assert get_refresh_token(new_refresh_token) is not None

    # teardown test case
    assert _test_teardown()


def test_run_wrf() -> None:
    """
    Test the RunWrf API action
    """
    # set up the test
    assert _test_setup()
    user, _ = _get_sample_user('regular')
    assert add_user_to_system(user)

    # create a request to get a user's own information
    ref_id = create_reference_id()
    request = {
        'configuration_name': 'test',
        'start_time': '2022-10-06 12:00:00',
        'forecast_length': 86400,
        'output_frequency': 1200,
        'notify': True
    }
    action = RunWrf(ref_id=ref_id, run_as_user=user, request=request)
    assert action.run()
    assert action.success

    # teardown the test
    assert _test_teardown()


# TODO: These two tests needs S3 access in the test environment -- need to consider a different testing method
# def test_get_wrf_meta_data() -> None:
#     """
#     Test the GetWrfMetaData action
#     """
#     # set up test case
#     assert _test_setup()
#     user, _ = _get_sample_user('regular')
#     assert add_user_to_system(user)
#
#     # create a request to get WRF meta data
#     request = {}
#
#     # create and run the action
#     action = GetWrfMetaData(run_as_user=user, request=request)
#     assert action.run()
#
#     # check the response value
#     assert action.success
#     assert 'configurations' in action.response
#     assert len(action.response['configurations']) == 1
#     assert 1654041600000 == action.response['configurations'][0]['cycle_times'][0]['cycle_time']
#     assert len(action.response['configurations'][0]['cycle_times'][0]['valid_times']) == 25
#
#     # teardown test case
#     assert _test_teardown()
# def test_get_wrf_geojson() -> None:
#     """
#     Test the GetWrfGeoJson action
#     """
#     # set up test case
#     assert _test_setup()
#     user, _ = _get_sample_user('regular')
#     assert add_user_to_system(user)
#
#     # create a request to get WRF meta data
#     request = {
#         'configuration': 'test',
#         'cycle_time': 1654041600000,
#         'valid_time': 1654041600000,
#         'variable': 'T2'
#     }
#
#     # create and run the action
#     action = GetWrfGeoJson(run_as_user=user, request=request)
#     assert action.run()
#
#     # check the response value
#     assert action.success
#     assert 'geojson' in action.response
#     assert action.response['geojson'] is not None
#     assert len(action.response['geojson']) == 403132
#     hash_alg = hashlib.sha256()
#     hash_alg.update(action.response['geojson'])
#     checksum = base64.b16encode(hash_alg.digest()).decode()
#     assert checksum == '21E2C5233E86C9E8187C2C907F96AE90AA0933340744C9E575C5F468CFDE79B1'
#
#     # teardown test case
#     assert _test_teardown()
