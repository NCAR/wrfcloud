import secrets
import wrfcloud.system
from wrfcloud.user import User, UserDao
from wrfcloud.user import add_user_to_system
from wrfcloud.user import get_user_from_system
from wrfcloud.user import update_user_in_system
from wrfcloud.user import delete_user_from_system
from wrfcloud.user import activate_user_in_system
from wrfcloud.user import is_reset_token_expired
from wrfcloud.user import new_reset_token
from wrfcloud.user import reset_password
from wrfcloud.user import add_user_reset_token


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
    user = _get_sample_admin_user()

    # add the user to the database
    assert add_user_to_system(user)

    # retrieve the user from the database
    user_ = get_user_from_system(email=user.get_email())

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
    user = _get_sample_admin_user()

    # add the user to the database
    assert add_user_to_system(user)

    # retrieve the user from the database
    user_ = get_user_from_system(email=user.get_email())

    # compare the original and retrieved user data
    for key in user.data:
        assert key in user_.data
        assert user.data[key] == user_.data[key]

    # update some user attributes
    user.set_role_id('readonly')
    user.set_name('dh')
    update_user_in_system(user)

    # retrieve the user from the database
    user_ = get_user_from_system(email=user.get_email())

    # check the updated fields
    assert user_.get_role_id() == 'readonly'
    assert user_.get_name() == 'dh'

    # update a user that does not exist in the database
    user.set_email('empty@ucar.edu')
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
    user = _get_sample_admin_user()

    # add the user to the database
    assert add_user_to_system(user)

    # retrieve the user from the database
    user_ = get_user_from_system(email=user.get_email())
    assert user_ is not None

    # delete the user from the database
    assert delete_user_from_system(user)

    # make sure the user is gone
    user_ = get_user_from_system(email=user.get_email())
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
    user = _get_sample_admin_user()

    # make sure the state is not active to begin with
    user.set_active(False)

    # add the user to the database
    assert add_user_to_system(user)

    # try to activate the user with a bogus activation key
    bogus_key = secrets.token_urlsafe(33)
    assert not activate_user_in_system(user.get_email(), bogus_key, 'new_password')

    # retrieve the user and make sure it is NOT active
    user_ = get_user_from_system(user.get_email())
    assert not user_.is_active()

    # try to activate the user with a valid activation key
    assert activate_user_in_system(user.get_email(), user.get_activation_key(), 'new_password')

    # retrieve the user and make sure it IS active
    user_ = get_user_from_system(user.get_email())
    assert user_.is_active()
    assert user_.validate_password('new_password')
    assert not user_.validate_password('old_password')

    # try to activate a user that does not exist in the database
    assert not activate_user_in_system('empty@ucar.edu', user.get_activation_key(), 'new_password')

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
    user = _get_sample_admin_user()
    user.set_active(True)

    # add the user to the database
    assert add_user_to_system(user)

    # try to reset password for a user that does not exist
    assert not reset_password('empty@ucar.edu', new_reset_token(1), 'new_password')

    # try to reset password for a user with a bogus reset token
    assert not reset_password(user.get_email(), new_reset_token(1), 'new_password')

    # try to reset password for a user with valid token
    assert add_user_reset_token(user)
    reset_token = user.get_reset_token()
    assert reset_password(user.get_email(), reset_token, 'new_password')

    # try to re-use the reset token to change password again
    assert not reset_password(user.get_email(), reset_token, 'another_new_password')

    # teardown the test resources
    assert _test_teardown()


def test_send_user_emails() -> None:
    """
    Test sending welcome and password reset emails to user
    :return: None
    """
    # Note: This probably will not work until the AWS account is setup, so expecting failure here

    # create a new user
    user = _get_sample_admin_user()
    user.set_reset_token(new_reset_token(8))

    # try to send emails
    assert not user.send_welcome_email()
    assert not user.send_password_reset_link()


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
        return dao.create_user_table()
    except Exception as e:
        print(e)
        return False

def test_sanitize() -> None:
    """
    Test the sanitize function
    :return: None
    """
    # create a new test user
    user = _get_sample_admin_user()
    user.set_reset_token(new_reset_token(8))
    user.data['extra_junk'] = 'evil_laugh'

    # check for all keys present
    for key in User.SANITIZE_KEYS:
        assert key in user.data

    # sanitize the user
    user.sanitize()

    # check for all keys not present
    for key in User.SANITIZE_KEYS:
        assert key not in user.data
    assert 'extra_junk' not in user.data


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
