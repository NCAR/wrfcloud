"""
Other code calling the wrfcloud.user module should mainly use functions from
this file.  Calling other functions and classes may have unexpected results.
"""

import secrets
import base64
import time
from typing import Union, List
from wrfcloud.user.user import User
from wrfcloud.user.user_dao import UserDao
from wrfcloud.log import Logger


log = Logger()


def add_user_to_system(new_user: User) -> bool:
    """
    Add a user to the system
    :param new_user: The new user to add
    :return True if added successfully
    """
    # get the DAOs
    dao = UserDao()

    # add the user and return status
    return dao.add_user(new_user)


def get_user_from_system(email: str) -> Union[User, None]:
    """
    Get a user from the system
    :param email: User email
    :return User with matching email, or None
    """
    # verify parameters
    if email is None:
        return None

    # get the user DAO
    dao = UserDao()

    # get user by email
    return dao.get_user_by_email(email)


def get_all_users_in_system() -> List[User]:
    """
    Get a list of all users in the system
    :return: A list of all users in the system
    """
    # create the data access object
    dao = UserDao()

    return dao.get_all_users()


def update_user_in_system(update_user: User) -> bool:
    """
    Use the DAOs to update a user in the system
    :param update_user: The complete user object with updated values (UID and email are immutable)
    :return: True if successful, otherwise False
    """
    # create objects
    dao = UserDao()

    # get the existing user
    existing_user = dao.get_user_by_email(update_user.email)
    if existing_user is None:
        log.error('The user does not exist and cannot be updated: ' + update_user.email)
        return False

    # update user table
    update_user.email = existing_user.email  # email is immutable
    updated = dao.update_user(update_user)

    return updated


def delete_user_from_system(del_user: User) -> bool:
    """
    Delete a user from the system
    :param del_user: User to delete from the system
    :return True if deleted, otherwise False
    """
    # get the user DAO
    dao = UserDao()

    # delete user
    if del_user is not None:
        return dao.delete_user(del_user)

    return False


def activate_user_in_system(email: str, activation_key: str, password: str) -> bool:
    """
    Attempt to verify a user's email address with emailed key
    :param email: User's email address
    :param activation_key: Provided verification key
    :param password: Set this new password if verified successfully
    :return: {bool} True if successful, otherwise False
    """
    try:
        # validate the provided input
        if len(activation_key) != 44:
            activation_key = _generate_salt()

        # get the user from the system
        u = get_user_from_system(email=email)

        # confirm the user exists
        if u is None:
            log.warn('Cannot validate an unknown user')
            u = User()
            u.activation_key = _generate_salt()

        # check that verification keys match
        matches = _secure_compare(activation_key, u.activation_key)

        # if it matches then attempt to update
        if matches:
            log.info('Verification key matches, updating datastore: %s' % u.email)
            u.active = True
            u.activation_key = _generate_salt()
            u.password = password
            return update_user_in_system(u)

    except Exception as e:
        log.error('Error verifying user: %s' % email, e)

    return False


def add_user_reset_token(u: User) -> bool:
    """
    Add a user reset token
    :param u: The user to add a reset token
    :return: {bool} True if added, otherwise False
    """
    u.reset_token = new_reset_token(hours=8)
    return update_user_in_system(u)


def reset_password(email: str, reset_token: str, new_plain_text: str) -> bool:
    """
    Reset a user's password with a reset token
    :param email: Email address of the user
    :param reset_token: User provided reset token
    :param new_plain_text: User provided new password in plain text
    :return: {str} New reset token
    """
    try:
        # verify the reset token is not expired
        if is_reset_token_expired(reset_token):
            log.info('Reset token is expired, password not updated')
            return False

        # get the user object
        dao = UserDao()
        user = dao.get_user_by_email(email)

        # create a fake user if email not found (help to prevent timing attacks)
        if user is None:
            user = User()
            user.reset_token = new_reset_token(-1)

        # update the password if reset token is valid
        if secrets.compare_digest(user.reset_token, reset_token):
            # change password in user object
            user.password = new_plain_text

            # set the reset token to None, so it gets removed from the database
            user.reset_token = None

            # try to update the user in the database
            return dao.update_user(user)

        # reset token does not match what we have saved
        return False
    except Exception as e:
        log.error('Failed to reset a password with a reset token', e)
        return False


def new_reset_token(hours: int) -> str:
    """
    Generate a new reset token good for N hours
    :param hours: Token to expire after N hours
    :return: New reset token
    """
    expire = str(int((3600*hours) + time.time()))
    token = _generate_salt()

    return expire + ';' + token


def is_reset_token_expired(reset_token: str) -> bool:
    """
    Determine if reset token is expired
    :param reset_token: Reset token
    :return: True if expired
    """
    (expire, *_) = reset_token.split(';')
    expire = int(expire)

    if expire > time.time() + (12*3600):
        return True

    return expire < time.time()


def _generate_salt(nbytes: int = 32) -> str:
    """
    Generate a new salt
    :param nbytes: Number of bytes in the new salt
    """
    return base64.b64encode(secrets.token_bytes(nbytes)).decode()


def _secure_compare(s1: str, s2: str) -> bool:
    """
    Compare strings in constant time
    :param s1: {str} String 1
    :param s2: {str} String 2
    :return: True if s1 and s2 are equal
    """
    return secrets.compare_digest(s1, s2)
