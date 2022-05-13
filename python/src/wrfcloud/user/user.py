"""
The User class is the data model used to represent a user and associated functions
"""

import base64
import secrets
import copy
import pkgutil
from typing import Union
import bcrypt
import wrfcloud.system
from wrfcloud.log import Logger


class User:
    """
    User data object
    """

    # list of fields to remove from the data
    SANITIZE_KEYS = ['role_id', 'password', 'reset_token', 'active', 'activation_key']

    def __init__(self, data: Union[dict, None] = None):
        """
        Initialize the user data object
        """
        # get a logger for this object
        self.log = Logger()

        # initialize the properties
        self.email: Union[str, None] = None
        self._pwhash: Union[bytes, None] = None
        self.role_id: Union[str, None] = None
        self.full_name: Union[str, None] = None
        self._reset_token: Union[str, None] = None
        self.active: Union[bool, None] = None
        self._activation_key: Union[str, None] = None

        # initialize from data if provided
        if data is not None:
            self.data = data

    @property
    def data(self):
        return {
            'email': self.email,
            'password': self.password,
            'role_id': self.role_id,
            'full_name': self.full_name,
            'reset_token': self.reset_token,
            'active': self.active,
            'activation_key': self.activation_key
        }

    @data.setter
    def data(self, data: dict):
        self.email = None if 'email' not in data else data['email']
        self.password = None if 'password' not in data else data['password']
        self.role_id = None if 'role_id' not in data else data['role_id']
        self.full_name = None if 'full_name' not in data else data['full_name']
        self.reset_token = None if 'reset_token' not in data else data['reset_token']
        self.active = None if 'active' not in data else data['active']
        self.activation_key = None if 'activation_key' not in data else data['activation_key']

    @property
    def password(self):
        return self._pwhash

    @password.setter
    def password(self, plain_text: Union[str, bytes]) -> None:
        """
        Set the password, only salted and hashed will be stored
        :param plain_text: Plain-text password
        """
        # clear the password if plain text is none or empty
        if plain_text is None or plain_text == '':
            self._pwhash = None
            return

        # set the password hash on the data object
        if isinstance(plain_text, bytes):
            # this is a byte array and not a string, so we expect it to be a hash already
            self._pwhash = plain_text
        else:
            self._pwhash = bcrypt.hashpw(plain_text.encode(), bcrypt.gensalt())

    @property
    def reset_token(self):
        return self._reset_token

    @reset_token.setter
    def reset_token(self, reset_token: str) -> None:
        """
        Set the reset token
        :param reset_token: Reset token
        """
        self._reset_token = None if reset_token is None or len(reset_token) < 44 else reset_token

    @property
    def activation_key(self) -> str:
        """
        Get the activation key and create a new one if it is not set yet
        :return Activation key
        """
        # create a verification key if it has not already been set
        if self._activation_key is None:
            self._activation_key = base64.b64encode(secrets.token_bytes(32)).decode()
        return self._activation_key

    @activation_key.setter
    def activation_key(self, activation_key: str) -> None:
        """
        Set the activation key
        :param activation_key: Activation key
        """
        self._activation_key = None if activation_key is None or len(activation_key) < 44 \
            else activation_key

    @property
    def sanitized_data(self) -> Union[dict, None]:
        """
        Remove any fields that should not be passed back to the user client
        :return True if user is sanitized
        """
        # get a copy of the data dictionary
        data = copy.deepcopy(self.data)

        try:
            # remove all the fields that should not be returned to the user
            for field in self.SANITIZE_KEYS:
                if field in data:
                    data.pop(field)
        except Exception:
            return None
        return data

    def validate_password(self, plain_text: str) -> bool:
        """
        Validate the user's password
        :param plain_text: Plain text password
        :return: True if password matches, otherwise False
        """
        try:
            return bcrypt.checkpw(plain_text.encode(), self._pwhash)
        except Exception:
            return False

    def send_password_reset_link(self) -> bool:
        """
        Send a password reset link
        """
        import pkgutil
        import urllib.request   # slow deferred import

        try:
            img = base64.b64encode(pkgutil.get_data('wrfcloud', 'resources/logo.jpg')).decode()
            html = pkgutil.get_data('wrfcloud', 'resources/email_templates/password_reset.html').decode()
            html = html.replace('__APP_NAME__', wrfcloud.system.APP_NAME)
            html = html.replace('__IMAGE_DATA__', img)
            html = html.replace('__APP_URL__', wrfcloud.system.APP_URL)
            html = html.replace('__EMAIL__', urllib.request.quote(self.email))
            html = html.replace('__RESET_TOKEN__', urllib.request.quote(self.reset_token))
            source = wrfcloud.system.SYSTEM_EMAIL_SENDER
            dest = {'ToAddresses': [self.email]}
            message = {
                'Subject': {
                    'Data': 'Password Reset Link',
                    'Charset': 'utf-8'
                },
                'Body': {
                    'Html': {
                        'Data': html, 'Charset': 'utf-8'
                    }
                }
            }

            session = wrfcloud.system.get_aws_session()
            ses = session.client('ses')
            ses.send_email(Source=source, Destination=dest, Message=message)

            return True
        except Exception as e:
            self.log.error('Failed to send password reset email.', e)
            return False

    def send_welcome_email(self) -> bool:
        """
        Send a welcome and activation email
        :return: None
        """
        import urllib.request   # slow deferred import

        try:
            img = base64.b64encode(pkgutil.get_data('wrfcloud', 'resources/logo.jpg')).decode()
            html = pkgutil.get_data('wrfcloud', 'resources/email_templates/welcome_email.html').decode()
            html = html.replace('__APP_NAME__', wrfcloud.system.APP_NAME)
            html = html.replace('__IMAGE_DATA__', img)
            html = html.replace('__APP_URL__', wrfcloud.system.APP_URL)
            html = html.replace('__EMAIL__', urllib.request.quote(self.email))
            html = html.replace('__ACTIVATION_KEY__', urllib.request.quote(self.activation_key))
            source = wrfcloud.system.SYSTEM_EMAIL_SENDER
            dest = {'ToAddresses': [self.email]}
            message = {
                'Subject': {
                    'Data': 'Verify Email Address',
                    'Charset': 'utf-8'
                },
                'Body': {
                    'Html': {
                        'Data': html, 'Charset': 'utf-8'
                    }
                }
            }

            session = wrfcloud.system.get_aws_session()
            ses = session.client('ses')
            ses.send_email(Source=source, Destination=dest, Message=message)

            return True
        except Exception as e:
            self.log.error('Failed to send welcome email.', e)
            return False
