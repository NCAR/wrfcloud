import secrets
import wrfcloud.system
from wrfcloud.user import User
from wrfcloud.user import add_user_to_system
from wrfcloud.user import get_user_from_system
from wrfcloud.user import update_user_in_system
from wrfcloud.user import delete_user_from_system
from wrfcloud.user import activate_user_in_system
from wrfcloud.user import is_reset_token_expired
from wrfcloud.user import new_reset_token
from wrfcloud.user import reset_password
from wrfcloud.user import add_user_reset_token
from helper import _test_setup, _test_teardown, _get_sample_user

# initialize the test environment
wrfcloud.system.init_environment(env='test')


def test_add_user() -> None:
    """
    Test the add user function
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # create sample user
    user, plain_text = _get_sample_user('admin')

    # add the user to the database
    assert add_user_to_system(user)

    # retrieve the user from the database
    user_ = get_user_from_system(email=user.email)

    # compare the original and retrieved user data
    for key in user.data:
        assert key in user_.data
        assert user.data[key] == user_.data[key]

    # test getting a user with no email address
    empty_email = ''
    if empty_email == '':
        empty_email = None
    assert get_user_from_system(empty_email) is None

    # teardown the test resources
    assert _test_teardown()


def test_update_user() -> None:
    """
    Test the operations to update and read a user
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # create sample user
    user, plain_text = _get_sample_user('admin')
    other_user, _ = _get_sample_user('regular')

    # add the user to the database
    assert add_user_to_system(user)

    # retrieve the user from the database
    user_ = get_user_from_system(email=user.email)

    # compare the original and retrieved user data
    for key in user.data:
        assert key in user_.data
        assert user.data[key] == user_.data[key]

    # update some user attributes
    user.role_id = other_user.role_id
    user.full_name = other_user.full_name
    update_user_in_system(user)

    # retrieve the user from the database
    user_ = get_user_from_system(email=user.email)

    # check the updated fields
    assert user_.role_id == other_user.role_id
    assert user_.full_name == other_user.full_name

    # update a user that does not exist in the database
    user.email = other_user.email
    assert not update_user_in_system(user)

    # teardown the test resources
    assert _test_teardown()


def test_delete_user() -> None:
    """
    Test deleting a user
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # create sample user
    user, plain_text = _get_sample_user('admin')

    # add the user to the database
    assert add_user_to_system(user)

    # retrieve the user from the database
    user_ = get_user_from_system(email=user.email)
    assert user_ is not None

    # delete the user from the database
    assert delete_user_from_system(user)

    # make sure the user is gone
    user_ = get_user_from_system(email=user.email)
    assert user_ is None

    # teardown the test resources
    assert _test_teardown()


def test_activate_user() -> None:
    """
    Test user activation
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # create sample user
    user, plain_text = _get_sample_user('admin')
    other_user, other_plain_text = _get_sample_user('regular')

    # make sure the state is not active to begin with
    user.active = False

    # add the user to the database
    assert add_user_to_system(user)

    # try to activate the user with a bogus activation key
    bogus_key = secrets.token_urlsafe(33)
    assert not activate_user_in_system(user.email, bogus_key, 'new_password')

    # retrieve the user and make sure it is NOT active
    user_ = get_user_from_system(user.email)
    assert not user_.active

    # try to activate the user with a valid activation key
    assert activate_user_in_system(user.email, user.activation_key, 'new_password')

    # retrieve the user and make sure it IS active
    user_ = get_user_from_system(user.email)
    assert user_.active
    assert user_.validate_password('new_password')
    assert not user_.validate_password('old_password')

    # try to activate a user that does not exist in the database
    assert not activate_user_in_system(other_user.email, user.activation_key, other_plain_text)

    # teardown the test resources
    assert _test_teardown()


def test_reset_tokens() -> None:
    """
    Test the password reset token functions
    :return: None
    """
    # create a token that is not expired
    token_nx = new_reset_token(1)

    # create a token that is expired
    token_x = new_reset_token(-1)

    # create a token that should evaluate to expired because its expiration exceeds the 12-hour max
    token_x2 = new_reset_token(24)

    # validate the expiry date of the tokens
    assert not is_reset_token_expired(token_nx)
    assert is_reset_token_expired(token_x)
    assert is_reset_token_expired(token_x2)


def test_password_reset() -> None:
    """
    Test the ability to reset a user password
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # create sample user
    user, plain_text = _get_sample_user('admin')
    user.active = True

    # add the user to the database
    assert add_user_to_system(user)

    # try to reset password for a user that does not exist
    assert not reset_password('empty@ucar.edu', new_reset_token(1), 'new_password')

    # try to reset password for a user with a bogus reset token
    assert not reset_password(user.email, new_reset_token(1), 'new_password')

    # try to reset password for a user with valid token
    assert add_user_reset_token(user)
    reset_token = user.reset_token
    assert reset_password(user.email, reset_token, 'new_password')

    # try to re-use the reset token to change password again
    assert not reset_password(user.email, reset_token, 'another_new_password')

    # teardown the test resources
    assert _test_teardown()


def test_send_user_emails() -> None:
    """
    Test sending welcome and password reset emails to user
    :return: None
    """
    # Note: This probably will not work until the AWS account is setup, so expecting failure here

    # create a new user
    user, plain_text = _get_sample_user('admin')
    user.reset_token = new_reset_token(8)

    # try to send emails
    assert user.send_welcome_email()
    assert user.send_password_reset_link()


def test_sanitize() -> None:
    """
    Test the sanitize function
    :return: None
    """
    # create a new test user
    user, plain_text = _get_sample_user('admin')
    user.reset_token = new_reset_token(8)

    # check for all keys present
    for key in User.SANITIZE_KEYS:
        assert key in user.data

    # sanitize the user
    sanitized_data = user.sanitized_data

    # check for all keys not present
    for key in User.SANITIZE_KEYS:
        assert key not in sanitized_data
