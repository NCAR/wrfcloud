import base64
import secrets
import json
import yaml
import pkgutil
from typing import Union

from wrfcloud.user import User
from wrfcloud.api.actions import Action
from wrfcloud.log import Logger
from wrfcloud.api.auth import get_user_from_jwt


def lambda_handler(event: dict, context: any) -> dict:
    """
    Take the appropriate action for the lambda call
    :param event: Event to the lambda
    :param context: Lambda context
    :return: Response
    """
    # create a logger
    log = Logger()

    # use the context value
    if context is None:
        log.debug('No context provided to Lambda Function')

    # parse out the request details
    request = json.loads(event['body'])
    action = request[Action.REQ_KEY_ACTION]
    jwt = request[Action.REQ_KEY_JWT] if Action.REQ_KEY_JWT in request else None
    data = request[Action.REQ_KEY_DATA]
    client_ip = event['requestContext']['identity']['sourceIp']

    # set a reference ID and the client IP instead of the app name
    ref_id = create_reference_id()
    log.set_application_name('%s %s' % (ref_id, client_ip))
    log.info('Starting action: %s' % action)

    # verify the session
    user = get_user_from_jwt(jwt)
    if user is None and jwt is not None:
        return create_invalid_session_response(ref_id)

    # attempt to run the action
    body = {}
    try:
        # determine if this user is authorized to run the action
        if not has_required_permissions(action, user):
            return create_unauthorized_action_response(ref_id)

        # create the action
        action_object = create_action(action, user, data)

        # run the action
        try:
            action_object.run()
        except Exception as e:
            log.error('Failed to run action', e)
            action_object.errors.append('General error')
            action_object.success = False

        # add the success flag to the response body
        body['ok'] = action_object.success

        # create the response body
        if action_object.success:
            body['data'] = action_object.response
        else:
            action_object.errors.append('Ref ID: %s' % ref_id)
            body['errors'] = action_object.errors

    except Exception as e:
        # handle an exception during action execution
        log.error('Failed to run the action', e)
        body['ok'] = False
        body['data'] = {}
        body['errors'] = ['General system error: %s' % ref_id]

    # create a proper lambda response
    response = {
        'isBase64Encoded': False,
        'headers': {
            'Content-Type': 'application/json',
            'Content-Encoding': 'identity'
        },
        'body': json.dumps(body)
    }

    # add CORS headers
    add_cors_headers(response)

    return response


def has_required_permissions(action: str, user: Union[User, None] = None) -> bool:
    """
    Determine if the run-as user has the required role to execute this action
    :param action: The action asking to be performed
    :param user: The user requesting the action
    :return: True if user has required permissions, otherwise False
    """
    # load the role definitions
    roles = yaml.full_load(pkgutil.get_data('wrfcloud', 'api/actions/roles.yaml'))

    # set the default role to anonymous
    role_name = 'anonymous'

    # override the role name if user is authenticated
    if user is not None:
        role_name = user.get_role_id()

    # check for unknown role value in the user
    log = Logger()
    if role_name not in roles:
        log.error('User is assigned to an unknown role: {user.get_email()}, {role_name}')
        return False

    # user has permissions if this class is listed in their role's permitted actions
    permitted_actions = roles[role_name]['permitted_actions']
    for permitted_action in permitted_actions:
        if permitted_action['action'] == action:
            return True
    return False


def create_reference_id():
    """
    Create a unique reference ID for this request to help find logs, etc
    :return: {str} A unique 10-character string
    """
    random = secrets.token_bytes(5)
    ref_id = base64.b16encode(random).decode()
    return ref_id


def create_action(action: str, user: User, data: dict) -> Union[Action, None]:
    """
    Create an action object
    :param action: Name of the action
    :param user: Run as user
    :param data: Request data
    :return: An action object or None
    """
    import importlib

    # create the action object
    try:
        action_package = 'wrfcloud.api.actions'
        action_class = getattr(importlib.import_module(action_package), action)
        action_object = action_class(run_as_user=user, request=data)
        return action_object
    except Exception as e:
        Logger().error('Error creating action: %s' % action, e)


def create_unauthorized_action_response(ref_id: str) -> dict:
    """
    Create a response that indicates the user is unauthorized to run that action
    :param ref_id: Request reference ID for error message
    :return: Unauthorized response
    """
    response = {
        'isBase64Encoded': False,
        'headers': {},
        'body': json.dumps(
            {
                'ok': False,
                'errors': ['This action is unauthorized', 'Ref ID: %s' % ref_id]
            }
        )
    }

    add_cors_headers(response)

    return response


def create_invalid_session_response(ref_id: str) -> dict:
    """
    Create a response that indicates the session is invalid
    :param ref_id: Request reference ID for error message
    :return: Invalid session response
    """
    response = {
        'isBase64Encoded': False,
        'headers': {},
        'body': json.dumps(
            {
                'ok': False,
                'errors': ['Please log in first', 'Ref ID: %s' % ref_id]
            }
        )
    }

    add_cors_headers(response)

    return response


def add_cors_headers(response):
    """
    Add CORS headers to the response
    :param response: The response must have a 'headers' entry
    :return: None
    """
    response['headers']['Access-Control-Allow-Origin'] = '*'
    response['headers']['Access-Control-Allow-Credentials'] = True
