"""
Actions related to users
"""

import secrets
from wrfcloud.api.actions.action import Action
from wrfcloud.user import User
from wrfcloud.user import get_user_from_system
from wrfcloud.user import get_all_users_in_system
from wrfcloud.user import add_user_to_system
from wrfcloud.user import update_user_in_system
from wrfcloud.user import delete_user_from_system


class CreateUser(Action):
    """
    Action used to create a new user in the system
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # check for required user parameter
        ok = self.check_request_fields(['user'], [])

        # check the user parameter values
        user_fields = ['email', 'role_id', 'full_name']
        ok = ok and self.check_request_fields(user_fields, [], self.request['user'])

        return ok

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        # create a new user object from the request data
        user = User(self.request['user'])

        # check if the email address provided is already in use
        existing_user = get_user_from_system(user.email)
        if existing_user is not None:
            self.log.error(f'User already exists with the given email address: {user.email}')
            self.errors.append('Email address is already in use')
            return False

        # update some other user fields
        user.password = None
        user.reset_token = None
        user.active = False

        # try to add the new user to the system and send a welcome email
        added = add_user_to_system(user)
        # TODO: Enable once AWS SES is active
        # emailed = added and user.send_welcome_email()

        # maybe log error messages
        if not added:
            self.log.error(f'Failed to add user to the system: {user.email}')
        # TODO: Enable once AWS SES is active
        # if not emailed:
        #     self.log.error(f'Failed to send welcome email to new user: {user.email}')

        # return success status
        # TODO: Enable once AWS SES is active
        # return added and emailed
        return added


class ActivateUser(Action):
    """
    Action used to verify a new user's email address and set up a new password
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # check for required parameters
        ok = self.check_request_fields(['email', 'activation_key', 'new_password'], [])

        # TODO: verify minimum password requirements -- overlaps with ChangePassword action
        if len(self.request['new_password']) < 10:
            ok = False
            self.errors.append('Password must be at least 10 characters long')

        return ok

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        # get the request parameters
        email = self.request['email']
        activation_key = self.request['activation_key']
        new_password = self.request['new_password']

        # get the existing user from the system
        user = get_user_from_system(email)

        # fail if we did not find the user
        if user is None:
            self.log.error(f'Could not find user in system: {email}')
            self.errors.append('Invalid activation key')
            return False

        # check current activation status
        if user.active:
            self.log.error(f'User is already active: {email}')
            self.errors.append('Account is already active')
            return False

        # check the activation key and set the new password
        if secrets.compare_digest(user.activation_key, activation_key):
            user.password = new_password
            user.activation_key = None
            user.active = True
            updated = update_user_in_system(user)
            if not updated:
                self.log.error('Failed to update user in system.')
                self.errors.append('General error')
            return updated


class ListUsers(Action):
    """
    Get a list of all the users in the system
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # No parameters are expected or allowed
        return self.check_request_fields([], [])

    def perform_action(self) -> bool:
        """
        Put a list of all system users in the response object
        :return: True if the action ran successfully
        """
        try:
            # get all the users from the system
            users = get_all_users_in_system()

            # put the sanitized user data into the response
            self.response['users'] = [user.sanitized_data for user in users]
        except Exception as e:
            self.log.error('Failed to get a list of users in the system', e)
            self.errors.append('General error')
            return False

        return True


class UpdateUser(Action):
    """
    Update a user in the system
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        ok = self.check_request_fields(['user'], [])
        ok = ok and self.check_request_fields(['email'], ['password', 'role_id', 'full_name'], self.request['user'])

        return ok

    def perform_action(self) -> bool:
        """
        Update a user with the fields in the request
        :return: True if the action ran successfully
        """
        # get the user email from the request
        user_data = self.request['user']
        email = user_data['email']

        # get the user we want to update
        user = get_user_from_system(email)

        # make sure we found a user with that email address
        if user is None:
            self.log.error(f'User not found in system with email: {email}')
            self.errors.append('Unknown user')
            return False

        # update any provided user fields
        user.update(user_data)

        # update the user in the system
        if update_user_in_system(user):
            user = get_user_from_system(email)
            self.response['user'] = user.sanitized_data
            return True

        # failed to update user
        self.log.error(f'Failed to update user with email address: ${email}')
        self.errors.append('User data not updated')
        return False


class DeleteUser(Action):
    """
    Delete a user from the system
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        return self.check_request_fields(['email'], [])

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        # get the email of the user to delete
        email = self.request['email']

        # get the user from the system
        user = get_user_from_system(email)

        # make sure we found the user
        if user is None:
            self.log.error(f'Unable to find user in system: {email}')
            self.errors.append('User not found')
            return False

        # delete the user from the system
        if delete_user_from_system(user):
            return True

        # general error removing user
        self.log.error('Failed to remove user from system')
        self.errors.append('General error')
        return False


class WhoAmI(Action):
    """
    Return information about the current user
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # No parameters are expected or allowed
        return self.check_request_fields([], [])

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        # get the most recent system data from the run_as_user
        user = get_user_from_system(self.run_as_user.email)

        # this should be an unusual and maybe even suspicious case
        if user is None:
            self.log.error('SECURITY: the run_as_user does not exist in the database?')
            self.errors.append('General error')
            return False

        # put the user information into the response
        self.response['user'] = user.sanitized_data

        # this action should really never fail
        return True


class AddPasswordResetToken(Action):
    """
    Add a password reset token to a user
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # make sure the request contains an email field
        return self.check_request_fields(['email'], [])

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        # get email address from the request
        email = self.request['email']

        # get user from the database based on email
        user = get_user_from_system(email)

        # when the last reset token was sent and limit to one per 10 minutes
        if user.get_seconds_since_reset_token_sent() < 600:
            self.log.error('Cannot add another reset token for at least 10 minutes')
            self.errors.append('An email was recently sent.')
            self.errors.append('Please check your spam folder.')
            self.errors.append('Another one cannot be sent for 10 minutes.')
            return False

        # set a new reset token and send an email with the information
        user.add_reset_token()
        updated = update_user_in_system(user)
        # TODO: Enable this once AWS SES is active
        # sent = user.send_password_reset_link()
        sent = True

        # check that things worked
        if not updated:
            self.log.error('Failed to update user database with a reset token')
            self.errors.append('General error')
        if not sent:
            self.log.error(f'Failed to send email to user at: {user.email}')
            self.errors.append('General error')

        # return status
        return updated and sent


class ResetPassword(Action):
    """
    Reset a forgotten password with an emailed token
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        return self.check_request_fields(['email', 'reset_token', 'new_password'], [])

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        # get the request parameters
        email = self.request['email']
        reset_token = self.request['reset_token']
        new_password = self.request['new_password']

        # get the user object from the system
        user = get_user_from_system(email)

        # make sure we found the user
        if user is None:
            self.log.error(f'User not found with email for password reset: {email}')
            self.errors.append('Password reset failed')
            return False

        # check the reset token of the user against the request's reset token
        if not user.validate_reset_token(reset_token):
            self.log.error(f'Invalid password reset token for user: {email} {reset_token}')
            self.errors.append('Password reset failed')
            return False

        # update the user's password
        user.password = new_password
        user.reset_token = None
        updated = update_user_in_system(user)

        # log errors if not updated
        if not updated:
            self.log.error(f'Failed to reset password for user: {email}')
            self.errors.append('Password reset failed')

        # return the status
        return updated
