"""
The following functions will sign and send a message to an API Gateway client.  This code is
derived from the example at the following URL:
https://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html
"""

import sys
import datetime
import urllib
import urllib.parse
import hmac
import hashlib
import requests
import boto3
from wrfcloud.log import Logger


log = Logger()


def _sign(key: bytes, msg: str) -> bytes:
    """
    Sign a message with the given key
    :param key: Key used for cryptographic signature
    :param msg: Message to be signed
    :return: Message signature
    """
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def _get_signature_key(key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
    """
    Create a signature key
    :param key: Key used for cryptographic signature
    :param date_stamp: Timestamp added to the signed message
    :param region_name: Region added to the signed message
    :param service_name: Service name added to the signed message
    :return: New signature key
    """
    k_date = _sign(('AWS4' + key).encode('utf-8'), date_stamp)
    k_region = _sign(k_date, region_name)
    k_service = _sign(k_region, service_name)
    k_signing = _sign(k_service, 'aws4_request')
    return k_signing


def send_message_to_ws_client(url: str, request_data: str) -> bool:
    """
    Post data to an API Gateway Websocket URL
    :param url: The full URL to the websocket callback
    :param request_data: The data to send
    :return: True if successful, otherwise False
    """
    # request values
    tokens = url.split('/')
    method = 'POST'
    service = 'execute-api'
    host = tokens[2]
    stage = tokens[3]
    endpoint = 'https://' + host
    connection_id = tokens[5]

    # get AWS credentials
    session = boto3.Session()
    region = session.region_name
    credentials = session.get_credentials()
    credentials = credentials.get_frozen_credentials()
    access_key = credentials.access_key
    secret_key = credentials.secret_key
    aws_token = credentials.token
    if access_key is None or secret_key is None:
        print('No credentials are available.')
        sys.exit()

    # create a date for headers and the credential string
    timenow = datetime.datetime.utcnow()
    amzdate = timenow.strftime('%Y%m%dT%H%M%SZ')
    datestamp = timenow.strftime('%Y%m%d')

    # create the canonical request
    canonical_uri = '/%s/@connections/%s' % (stage, connection_id)
    canonical_headers = 'host:' + host + '\n' + 'x-amz-date:' + amzdate + '\n'
    signed_headers = 'host;x-amz-date'
    if aws_token:
        canonical_headers += 'x-amz-security-token:' + aws_token + '\n'
        signed_headers += ';x-amz-security-token'
    payload_hash = hashlib.sha256(request_data.encode('utf-8')).hexdigest()
    canonical_request = method + '\n' + urllib.parse.quote(canonical_uri) + '\n\n' + \
        canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    # create the string to sign
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = datestamp + '/' + region + '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' + amzdate + '\n' + credential_scope + '\n' + \
        hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    # compute and sign the signature
    signing_key = _get_signature_key(secret_key, datestamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256)\
        .hexdigest()

    # add signing information to the request
    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + \
        credential_scope + ', ' + 'SignedHeaders=' + signed_headers + ', ' +\
        'Signature=' + signature
    headers = {'x-amz-date': amzdate, 'Authorization': authorization_header}
    if aws_token:
        headers['X-Amz-Security-Token'] = aws_token

    # send the request
    try:
        request_url = endpoint + canonical_uri
        response = requests.post(request_url, headers=headers, data=request_data)

        # check the response
        if response.status_code != 200:
            log.warn(f'Failed to send message to client: {response.status_code}')
            return False
    except Exception as e:
        log.warn('Failed to provide status update to client', e)

    return True
