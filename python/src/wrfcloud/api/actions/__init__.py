"""
This module contains all the Action classes for the API.
"""

__all__ = ['Action', 'Login', 'ChangePassword', 'CreateUser', 'ActivateUser', 'ListUsers',
           'UpdateUser', 'DeleteUser', 'WhoAmI', 'AddPasswordResetToken', 'ResetPassword']

from wrfcloud.api.actions.action import Action
from wrfcloud.api.actions.login import Login
from wrfcloud.api.actions.password import ChangePassword
from wrfcloud.api.actions.users import CreateUser
from wrfcloud.api.actions.users import ActivateUser
from wrfcloud.api.actions.users import ListUsers
from wrfcloud.api.actions.users import UpdateUser
from wrfcloud.api.actions.users import DeleteUser
from wrfcloud.api.actions.users import WhoAmI
from wrfcloud.api.actions.users import AddPasswordResetToken
from wrfcloud.api.actions.users import ResetPassword
