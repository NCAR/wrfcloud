import os
import secrets
from wrfcloud.api.actions import Login
from wrfcloud.api.actions import ChangePassword
from wrfcloud.api.actions import CreateUser
from wrfcloud.api.actions import ActivateUser
from wrfcloud.api.actions import ListUsers
from wrfcloud.api.actions import UpdateUser
from wrfcloud.api.actions import DeleteUser
from wrfcloud.api.actions import WhoAmI
from wrfcloud.api.actions import AddPasswordResetToken
from wrfcloud.api.actions import ResetPassword
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
    request = {'email': user.email, 'password': plain_text}
    login = Login(run_as_user=None, request=request)
    assert login.run()
    user_ = get_user_from_jwt(login.response['jwt'])
    assert user.email == user_.email

    # create the request and run the action - wrong password
    request = {'email': user.email, 'password': 'wr0nGP@$Sw0RD!'}
    login = Login(run_as_user=None, request=request)
    assert not login.run()
    assert 'jwt' not in login.response

    # create the request and run the action - email not in system
    assert delete_user_from_system(user)
    request = {'email': user.email, 'password': plain_text}
    login = Login(run_as_user=None, request=request)
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
    request = {
        'password0': plain_text,
        'password1': 'mys@f#newpasw#rd',
        'password2': 'mys@f#newpasw#rd'
    }
    chpass = ChangePassword(run_as_user=user, request=request)
    assert chpass.run()

    # check that the password was really changed
    user_ = get_user_from_system(user.email)
    assert user_.validate_password('mys@f#newpasw#rd')

    # create the request and run the action - change anonymous user password
    request = {
        'password0': '1000$moustacheCOMB',
        'password1': 'mys@f#newpasw#rd',
        'password2': 'mys@f#newpasw#rd'
    }
    chpass = ChangePassword(request=request)
    assert not chpass.run()

    # create the request and run the action - new passwords do not match
    request = {
        'password0': 'mys@f#newpasw#rd',
        'password1': 'fdsafdsafdsa',
        'password2': 'asdfasdfasdf'
    }
    chpass = ChangePassword(run_as_user=user, request=request)
    assert not chpass.run()

    # check that the password was not changed
    user_ = get_user_from_system(user.email)
    assert user_.validate_password('mys@f#newpasw#rd')

    # create the request and run the action - invalid current password
    request = {
        'password0': 'myWRONGpasw#rd',
        'password1': 'asdfasdfasdf',
        'password2': 'asdfasdfasdf'
    }
    chpass = ChangePassword(run_as_user=user, request=request)
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
    request = {
        'email': user.email,
        'wrong_key': plain_text
    }
    login = Login(request=request)
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
    request = {
        'user': {
            'full_name': reg_user.full_name,
            'email': reg_user.email,
            'role_id': reg_user.role_id
        }
    }

    # create and run the action
    action = CreateUser(run_as_user=admin, request=request)
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
    request = {
        'email': user.email,
        'activation_key': user.activation_key,
        'new_password': user_pw
    }
    action = ActivateUser(run_as_user=None, request=request)
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
    request = {
        'user': {
            'full_name': reg_user.full_name,
            'email': admin.email,
            'role_id': reg_user.role_id
        }
    }
    action = CreateUser(run_as_user=admin, request=request)
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
    request = {
        'email': admin.email,
        'activation_key': admin.activation_key,
        'new_password': plain_text
    }
    action = ActivateUser(run_as_user=None, request=request)
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
    request = {
        'email': admin.email,
        'activation_key': admin.activation_key,
        'new_password': 'abc123'
    }
    action = ActivateUser(run_as_user=None, request=request)
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
    request = {
        'email': reg_user.email,
        'activation_key': reg_user.activation_key,
        'new_password': plain_text
    }
    action = ActivateUser(run_as_user=None, request=request)
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
    request = {}
    action = ListUsers(run_as_user=admin, request=request)
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
    request = {
        'user': {
            'email': user.email,
            'full_name': 'Joe Bauers'
        }
    }
    action = UpdateUser(run_as_user=admin, request=request)
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
    request = {
        'user': {
            'email': user.email,
            'full_name': 'Joe Bauers'
        }
    }
    action = UpdateUser(run_as_user=admin, request=request)
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
    request = {'email': user.email}
    action = DeleteUser(run_as_user=admin, request=request)
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
    request = {'email': user.email}
    action = DeleteUser(run_as_user=admin, request=request)
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
    request = {}
    action = WhoAmI(run_as_user=user, request=request)
    assert action.run()
    assert action.success
    assert 'user' in action.response
    assert 'active' not in action.response['user']

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
    request = {'email': user.email}
    action = AddPasswordResetToken(run_as_user=None, request=request)
    assert action.run()
    assert action.success
    user_ = get_user_from_system(user.email)
    assert user_.get_seconds_since_reset_token_sent() < 10
    token = user_.reset_token.split(';')[1]
    assert user_.validate_reset_token(token)

    # try to set another reset token too quickly
    action = AddPasswordResetToken(run_as_user=None, request=request)
    assert not action.run()
    assert not action.success
    assert 'An email was recently sent.' in action.errors

    # user the reset token to reset the password
    request = {
        'email': user_.email,
        'reset_token': user_.reset_token.split(';')[1],
        'new_password': '100shredsOFcabbage'
    }
    action = ResetPassword(run_as_user=None, request=request)
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
    request = {
        'email': 'unknown@example.com',
        'reset_token': User().reset_token,
        'new_password': '100shredsOFcabbage'
    }
    action = ResetPassword(run_as_user=None, request=request)
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
    request = {
        'email': user.email,
        'reset_token': User().reset_token,
        'new_password': '100shredsOFcabbage'
    }
    action = ResetPassword(run_as_user=None, request=request)
    assert not action.run()
    assert not action.success
    assert 'Password reset failed' in action.errors

    # test with a valid reset token set in the system user
    user.reset_token = User().reset_token
    assert update_user_in_system(user)
    request = {
        'email': user.email,
        'reset_token': User().reset_token,  # get a random token value
        'new_password': '100shredsOFcabbage'
    }
    action = ResetPassword(run_as_user=None, request=request)
    assert not action.run()
    assert not action.success
    assert 'Password reset failed' in action.errors

    # teardown test case
    assert _test_teardown()
