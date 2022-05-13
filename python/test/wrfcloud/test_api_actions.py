import os
import secrets
from wrfcloud.api.actions import Login
from wrfcloud.api.actions import ChangePassword
from wrfcloud.user import User
from wrfcloud.user import UserDao
from wrfcloud.user import add_user_to_system
from wrfcloud.user import get_user_from_system
from wrfcloud.user import delete_user_from_system
from wrfcloud.system import init_environment
from wrfcloud.api.auth import get_user_from_jwt


init_environment(env='test')
os.environ['JWT_KEY'] = secrets.token_hex(64)


def test_login() -> None:
    """
    Test the login action
    :return: None
    """
    # set up the test
    assert _test_setup()
    user = _get_sample_admin_user()
    assert add_user_to_system(user)

    # create the request and run the action - valid login
    request = {'email': 'hahnd+wrfcloudtest@ucar.edu', 'password': '1000$moustacheCOMB'}
    login = Login(run_as_user=None, request=request)
    assert login.run()
    user_ = get_user_from_jwt(login.response['jwt'])
    assert user.email == user_.email

    # create the request and run the action - wrong password
    request = {'email': 'hahnd+wrfcloudtest@ucar.edu', 'password': 'wr0nGP@$Sw0RD!'}
    login = Login(run_as_user=None, request=request)
    assert not login.run()
    assert 'jwt' not in login.response

    # create the request and run the action - email not in system
    request = {'email': 'hahnd+somebodyelse@ucar.edu', 'password': '1000$moustacheCOMB'}
    login = Login(run_as_user=None, request=request)
    assert not login.run()
    assert 'jwt' not in login.response

    # teardown the test
    assert delete_user_from_system(user)
    assert _test_teardown()


def test_change_password() -> None:
    """
    Test the change password action
    :return: None
    """
    # set up the test
    assert _test_setup()
    user = _get_sample_admin_user()
    assert add_user_to_system(user)

    # create the request and run the action - valid change password
    request = {
        'password0': '1000$moustacheCOMB',
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
    user = _get_sample_admin_user()
    assert add_user_to_system(user)

    # create the request and run the action - invalid request parameters
    request = {
        'email': user.email,
        'wrong_key': '1000$moustacheCOMB'
    }
    login = Login(request=request)
    assert not login.run()
    assert not login.success
    assert 'jwt' not in login.response

    # teardown the test
    assert delete_user_from_system(user)
    assert _test_teardown()


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
    password = '1000$moustacheCOMB'
    user = User()
    user.full_name = 'David Hahn'
    user.email = 'hahnd+wrfcloudtest@ucar.edu'
    user.password = password
    user.role_id = 'admin'
    user.active = False
    user.activation_key = secrets.token_urlsafe(33)

    # make sure the password was hashed
    assert user.password != password

    return user
