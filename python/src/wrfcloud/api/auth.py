"""
Functions to create and validate JSON Web Tokens (JWT)
"""

import os
import secrets
from datetime import datetime
from typing import Union
import jwt
from wrfcloud.log import Logger
from wrfcloud.user import User, get_user_from_system


KEY_EMAIL = 'email'
KEY_EXPIRES = 'expires'
KEY_ROLE = 'role'


def create_jwt(payload: dict, expiration: int = 3600) -> str:
    """
    Get a new JSON web token
    :param payload: Payload to put into the new JWT -- Payload should not include expiration
    :param expiration: Expiration time in seconds from now
    :return: Base64-encoded JWT
    """
    # add/overwrite expiration field
    payload[KEY_EXPIRES] = round(datetime.utcnow().timestamp()) + expiration

    # encode the JWT
    key = os.environ['JWT_KEY'] if 'JWT_KEY' in os.environ else secrets.token_hex(64)
    token = jwt.encode(payload, key).decode()

    # maybe log a warning
    if 'JWT_KEY' not in os.environ:
        Logger().warn('JWT_KEY is not set.  Issued JWTs will not be valid.')

    return token


def validate_jwt(token: str) -> Union[dict, None]:
    """
    Validate the token
    :param token: Token value
    :return: JWT payload IF valid, otherwise None
    """
    try:
        # No token = anonymous user
        if token is None:
            return None

        key = os.environ['JWT_KEY'] if 'JWT_KEY' in os.environ else secrets.token_hex(64)
        payload = jwt.decode(token, key, verify=True)
        now = datetime.utcnow().timestamp()

        if KEY_EXPIRES in payload:
            if payload[KEY_EXPIRES] >= now:
                if KEY_EMAIL in payload:
                    return payload
    except Exception as e:
        log = Logger()
        log.error('Failed to validate JWT')
        log.error(e)

    return None


def get_user_from_jwt(token: str) -> Union[User, None]:
    """
    Get a user from the given JWT
    :param token: The unvalidated JWT
    :return: User authenticated by the JWT, or None
    """
    payload = validate_jwt(token)
    user = None if payload is None else get_user_from_system(payload[KEY_EMAIL])

    return user
