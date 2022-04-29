"""
The User class is the data model used to represent a user and associated functions
"""

import base64
import secrets
import bcrypt
import copy
from typing import Union
import wrfcloud.system
from wrfcloud.log import Logger


class User:
    """
    User data object
    """

    # Constant values
    USER_ID_LENGTH = 16
    SALT_LENGTH = 24
    DEFAULT_ROUNDS = 8

    # Field ID constants
    KEY_EMAIL = 'email'
    KEY_PASSWORD = 'pwhash'
    KEY_ROLE_ID = 'role_id'
    KEY_FULL_NAME = 'fullname'
    KEY_RESET_TOKEN = 'reset_token'
    KEY_ACTIVE = 'active'
    KEY_ACTIVATION_KEY = 'activation_key'

    # list of all the valid fields
    ALL_KEYS = [KEY_ROLE_ID, KEY_EMAIL, KEY_PASSWORD, KEY_FULL_NAME, KEY_RESET_TOKEN,
                KEY_ACTIVATION_KEY, KEY_ACTIVE]

    # Sanitize keys are removed during the sanitize function, which
    # should be called before the API returns data to any client
    SANITIZE_KEYS = [KEY_ROLE_ID, KEY_PASSWORD, KEY_RESET_TOKEN, KEY_ACTIVE, KEY_ACTIVATION_KEY]

    def __init__(self, data: dict = None):
        """
        Initialize the user data object
        """
        self.log = Logger()
        self.data = {}
        if data is not None:
            self.data = copy.deepcopy(data)
            self.prune()

    def get_role_id(self) -> Union[str, None]:
        """
        Get the role id
        :return: {str} The role id
        """
        return self.data[User.KEY_ROLE_ID]

    def set_role_id(self, rid: str) -> None:
        """
        Set the role ID
        :param rid: Role ID value
        """
        self.data[User.KEY_ROLE_ID] = rid

    def get_name(self) -> Union[str, None]:
        """
        Get the user name
        :return: {str} The user name
        """
        return self.data[User.KEY_FULL_NAME]

    def set_name(self, name: str) -> None:
        """
        Set the user name
        :return: {str} The user name
        """
        self.data[User.KEY_FULL_NAME] = name

    def get_email(self) -> Union[str, None]:
        """
        Get the user email
        :return: {str} The user email
        """
        return self.data[User.KEY_EMAIL]

    def set_email(self, email: str) -> None:
        """
        Set the user email
        :return: {str} The user email
        """
        self.data[User.KEY_EMAIL] = email

    def set_password(self, plain_text: str) -> None:
        """
        Set the password, only salted and hashed will be stored
        :param plain_text: Plain-text password
        """
        # set the password hash on the data object
        self.data[User.KEY_PASSWORD] = bcrypt.hashpw(plain_text.encode(), bcrypt.gensalt())

    def get_reset_token(self) -> str:
        """
        Get the reset token
        :return Reset token
        """
        return self.data[User.KEY_RESET_TOKEN] if User.KEY_RESET_TOKEN in self.data else None

    def set_reset_token(self, reset_token: str) -> None:
        """
        Set the reset token
        :param reset_token: Reset token
        """
        if len(reset_token) < 44:
            if User.KEY_RESET_TOKEN in self.data:
                self.data.pop(User.KEY_RESET_TOKEN)
            return
        self.data[User.KEY_RESET_TOKEN] = reset_token

    def get_activation_key(self) -> str:
        """
        Get the verification key
        :return Verification key
        """
        # create a verification key if it has not already been set
        if User.KEY_ACTIVATION_KEY not in self.data:
            self.data[User.KEY_ACTIVATION_KEY] = base64.b64encode(secrets.token_bytes(32)).decode()
        return self.data[User.KEY_ACTIVATION_KEY]

    def set_activation_key(self, verification_key: str) -> None:
        """
        Set the verification key
        :param verification_key: Verification key
        """
        if len(verification_key) < 44:
            if User.KEY_ACTIVATION_KEY in self.data:
                self.data.pop(User.KEY_ACTIVATION_KEY)
            return
        self.data[User.KEY_ACTIVATION_KEY] = verification_key

    def is_active(self) -> bool:
        """
        Check active flag
        :return True if user was activated
        """
        return False if User.KEY_ACTIVE not in self.data else self.data[User.KEY_ACTIVE]

    def set_active(self, active: bool) -> None:
        """
        Set active user flag
        """
        self.data[User.KEY_ACTIVE] = active

    def validate_password(self, plain_text: str) -> bool:
        """
        Validate the user's password
        :param plain_text: Plain text password
        :return: True if password matches, otherwise False
        """
        try:
            return bcrypt.checkpw(plain_text.encode(), self.data[User.KEY_PASSWORD])
        except Exception:
            return False

    def prune(self) -> bool:
        """
        Remove any superfluous fields
        :return True if user is pruned
        """
        try:
            pop_fields = []
            for key in self.data:
                if key not in User.ALL_KEYS:
                    pop_fields.append(key)
            for pop_field in pop_fields:
                self.data.pop(pop_field)
        except Exception:
            return False
        return True

    def sanitize(self) -> bool:
        """
        Remove any fields that should not be passed back to the user client
        :return True if user is sanitized
        """
        pruned = self.prune()

        try:
            for field in User.SANITIZE_KEYS:
                if field in self.data:
                    self.data.pop(field)
        except Exception:
            return False
        return pruned

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
            html = html.replace('__EMAIL__', urllib.request.quote(self.get_email()))
            html = html.replace('__RESET_TOKEN__', urllib.request.quote(self.get_reset_token()))
            source = wrfcloud.system.SYSTEM_EMAIL_SENDER
            dest = {'ToAddresses': [self.get_email()]}
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
        import wrfcloud.system
        import pkgutil
        import urllib.request   # slow deferred import

        try:
            img = base64.b64encode(pkgutil.get_data('wrfcloud', 'resources/logo.jpg')).decode()
            html = pkgutil.get_data('wrfcloud', 'resources/email_templates/welcome_email.html').decode()
            html = html.replace('__APP_NAME__', wrfcloud.system.APP_NAME)
            html = html.replace('__IMAGE_DATA__', img)
            html = html.replace('__APP_URL__', wrfcloud.system.APP_URL)
            html = html.replace('__EMAIL__', urllib.request.quote(self.get_email()))
            html = html.replace('__ACTIVATION_KEY__', urllib.request.quote(self.get_activation_key()))
            source = wrfcloud.system.SYSTEM_EMAIL_SENDER
            dest = {'ToAddresses': [self.get_email()]}
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
