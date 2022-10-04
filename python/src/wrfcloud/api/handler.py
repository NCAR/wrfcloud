"""
Functions to handle API requests and provide a response
"""

import base64
import gzip
import secrets
import json
import pkgutil
from typing import Union
from datetime import datetime
import yaml
from wrfcloud.user import User
from wrfcloud.api.actions import Action
from wrfcloud.log import Logger
from wrfcloud.api.auth import get_user_from_jwt, get_jwt_payload, create_jwt
from wrfcloud.api.audit import AuditEntry, save_audit_log_entry


def lambda_handler(event: dict, context: any) -> dict:
    """
    Take the appropriate action for the lambda call
    :param event: Event to the lambda
    :param context: Lambda context
    :return: Response
    """
    # create a logger
    log = Logger()

    # create an audit log entry
    audit = AuditEntry()
    audit.start_time = datetime.timestamp(datetime.utcnow())

    # use the context value
    if context is None:
        log.debug('No context provided to Lambda Function')

    # parse out the request details
    request = Request(event)
    audit.action = request.action
    audit.ip_address = request.client_ip

    # set a reference ID and the client IP instead of the app name
    ref_id = create_reference_id()
    audit.ref_id = ref_id
    log.set_application_name(f'{ref_id} {request.client_ip}')
    log.info('Starting action: %s' % request.action)

    # verify the session
    user = get_user_from_jwt(request.jwt)
    if user is None and request.jwt is not None:
        return create_invalid_session_response(ref_id)

    # update audit log entry with auth info
    audit.authenticated = user is not None
    if user is not None:
        audit.username = user.email

    # attempt to run the action
    body = {}
    try:
        # determine if this user is authorized to run the action
        if not has_required_permissions(request.action, user):
            return create_unauthorized_action_response(ref_id)

        # create the action
        action_object = create_action(request, user, context)

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

    # update the audit log entry
    audit.end_time = datetime.timestamp(datetime.utcnow())
    audit.duration_ms = int(1000 * (audit.end_time - audit.start_time))
    audit.action_success = body['ok']

    # save the audit log entry
    try:
        if not save_audit_log_entry(audit):
            log.warn('Failed to save audit log entry: ' + json.dumps(audit.data))
    except Exception as e:
        log.warn('Failed to save audit log entry: ' + json.dumps(audit.data), e)

    # create a proper lambda response
    response = {
        'isBase64Encoded': True,
        'headers': {
            'Content-Type': 'application/json',
            'Content-Encoding': 'gzip'
        },
        'body': base64.b64encode(gzip.compress(json.dumps(body).encode()))
    }

    # add CORS headers
    add_cors_headers(response)

    return response


class Request:
    """
    Contains standard reqeust properties and can parse Lambda events from multiple sources
    """

    def __init__(self, event: dict) -> None:
        """
        Parse the Lambda event
        """
        # save the event object
        self.event = event

        # initialize the standard request properties
        self.action: Union[str, None] = None
        self.jwt: Union[str, None] = None
        self.data: Union[dict, None] = None
        self.client_ip: Union[str, None] = None
        self.client_url: Union[str, None] = None
        self.is_websocket: bool = False

        # poke around and detect the lambda event source
        if 'source' in event and event['source'] == 'aws.events':
            self._parse_from_eventbridge()
        elif 'body' in event and 'connectionId' in event['requestContext']:
            self._parse_from_apigateway_websocket()
        elif 'body' in event:
            self._parse_from_apigateway_rest()
        else:
            print(self.event)
            raise ValueError('Cannot determine source of event')

    def _parse_from_eventbridge(self):
        """
        Parse the request from an EventBridge source event
        """
        # get the request data from the "detail" part of the event
        request = self.event['request']
        self.action = request[Action.REQ_KEY_ACTION]
        self.jwt = request[Action.REQ_KEY_JWT] if Action.REQ_KEY_JWT in request else None
        self.data = request[Action.REQ_KEY_DATA]

        # create a new valid jwt for the user who scheduled this event
        payload = get_jwt_payload(self.jwt, True)
        if 'expires' in payload:
            payload.pop('expires')
        self.jwt = create_jwt(payload)

    def _parse_from_apigateway_rest(self):
        """
        Parse the request from an API Gateway REST source event
        """
        request = json.loads(self.event['body'])
        self.action = request[Action.REQ_KEY_ACTION]
        self.jwt = request[Action.REQ_KEY_JWT] if Action.REQ_KEY_JWT in request else None
        self.data = request[Action.REQ_KEY_DATA]
        self.client_ip = self.event['requestContext']['identity']['sourceIp']

    def _parse_from_apigateway_websocket(self):
        """
        Parse the request from an API Gateway V2 Websocket source event
        """
        # part is the same as API Gateway REST source event, so run that code first
        self._parse_from_apigateway_rest()

        # this is a websocket event
        self.is_websocket = True

        # put together a client URL
        domain_name = self.event['requestContext']['domainName']
        stage = self.event['requestContext']['stage']
        connection_id = self.event['requestContext']['connectionId']
        self.client_url = f'https://{domain_name}/{stage}/@connections/{connection_id}'


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
        role_name = user.role_id

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


def create_reference_id() -> str:
    """
    Create a unique reference ID for this request to help find logs, etc
    :return: A unique 10-character string
    """
    random = secrets.token_bytes(5)
    ref_id = base64.b16encode(random).decode()
    return ref_id


def create_action(request: Request, user: User, lambda_context: any) -> Union[Action, None]:
    """
    Create an action object
    :param request: Request object
    :param user: Run as user
    :param lambda_context: Lambda context or None
    :return: An action object or None
    """
    import importlib  # slow deferred import

    # create the action object
    try:
        action_package = 'wrfcloud.api.actions'
        action_class = getattr(importlib.import_module(action_package), request.action)
        action_object: Action = action_class(run_as_user=user, request=request.data, client_url=request.client_url)
        action_object.additional['lambda_context'] = lambda_context
        return action_object
    except Exception as e:
        Logger().error('Error creating action: %s' % request.action, e)

    return None


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
