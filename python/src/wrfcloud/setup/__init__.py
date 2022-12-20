__all__ = ['aws', 'setup']

import yaml
import getpass
from time import sleep
from concurrent.futures import Future, ThreadPoolExecutor
from typing import List, Union
from wrfcloud.system import init_environment, get_aws_session
from wrfcloud.aws.imagebuilder import WrfCloudImageBuilder
from wrfcloud.aws.imagebuilder import CloudFormation
from wrfcloud.user import add_user_to_system, User


def setup():
    """
    Setup WRF Cloud in the current AWS account
    """
    # Initialize the environment
    init_environment('production')
    user_data = {}

    # Collect input parameters - custom domain names (app, api, ws); admin email/password
    _setup_get_user_data(user_data)

    # Image Builder - create stack and run image builder pipeline
    print('Creating WRF Image...')
    image_builder = WrfCloudImageBuilder()
    image_builder.create_stack()
    image_builder.build_image()

    # CloudFormation - Data stack
    data_stack = CloudFormation()
    data_stack.stack_name = 'WrfCloudApiData'
    data_stack.cf_template_resource = 'setup/aws/cf_wrfcloud_data.yaml'
    data_stack.parameters.append({'ParameterKey': 'AppName', 'ParameterValue': 'wrfcloud'})
    data_stack.parameters.append({'ParameterKey': 'DeploymentType', 'ParameterValue': 'production'})
    data_stack.create_stack()

    # CloudFormation - Certificate stack - DNS certificate verification
    certificate_stack = WrfCloudCertificates(user_data['hosted_zone_id'])
    certificate_stack.stack_name = 'WrfCloudWebCertificate'
    certificate_stack.cf_template_resource = 'setup/aws/cf_wrfcloud_certificate.yaml'
    certificate_stack.parameters.append({'ParameterKey': 'DomainName', 'ParameterValue': user_data['domain']})
    certificate_stack.parameters.append({'ParameterKey': 'WebHostName', 'ParameterValue': user_data['app_domain']})
    certificate_stack.parameters.append({'ParameterKey': 'ApiHostName', 'ParameterValue': user_data['api_domain']})
    certificate_stack.parameters.append({'ParameterKey': 'WebsocketHostName', 'ParameterValue': user_data['ws_domain']})
    tpe = ThreadPoolExecutor(max_workers=1)
    validate_future = tpe.submit(certificate_stack.validate_certificates)
    certificate_stack.create_stack()
    validate_future.result()

    # CloudFormation - Web application stack

    # Enable SES identity
    _add_email_identity(user_data['admin_email'])
    _wait_for_email_identity_confirmation(user_data['admin_email'])

    # Create admin user
    admin = User()
    admin.full_name = user_data['full_name']
    admin.email = user_data['admin_email']
    admin.password = user_data['admin_password']
    admin.role_id = 'admin'
    admin.active = True
    add_user_to_system(admin)

    # Deploy web application


def _setup_get_user_data(user_data: dict):
    """
    Ask the user to enter parameters
    :param user_data: User data will be added into here
    """
    # get domain data
    hosted_zone_id, domain, app_domain, api_domain, ws_domain = _setup_get_domain_user_data()
    user_data['hosted_zone_id'] = hosted_zone_id
    user_data['domain'] = domain
    user_data['app_domain'] = app_domain
    user_data['api_domain'] = api_domain
    user_data['ws_domain'] = ws_domain

    full_name, email, password = _setup_get_admin_data()
    user_data['full_name'] = full_name
    user_data['admin_email'] = email
    user_data['admin_password'] = password

    # print a summary of the entries
    pw = user_data['admin_password']
    user_data['admin_password'] = '*'
    print(yaml.dump(user_data, indent=2))
    user_data['admin_password'] = pw


def _setup_get_domain_user_data() -> (str, str, str, str, str):
    """
    Ask the user to enter domain parameters
    :return: User entered domain and hostname data
    """
    # setup placeholders for user values
    print('Custom domain setup\n-------------------')
    hosted_zone_id: str = ''
    domain: str = ''
    app_domain: str = ''
    api_domain: str = ''
    ws_domain: str = ''

    # get the domain and hosted zone ID selection
    domains = _get_available_domains()
    print(f'Which domain name would you like to use? [1-{len(domains)}]')
    for i in range(len(domains)):
        print(str(i+1) + '. ' + domains[i]['Name'])
    domain_choice: int = int(_get_input(f'Enter choice [1-{len(domains)}]: ', default='1', min=1, max=len(domains))) - 1
    hosted_zone_id = domains[domain_choice]['Id'].split('/')[-1]
    domain = domains[domain_choice]['Name'][:-1]

    # get the application subdomain value
    while not app_domain.endswith(domain):
        app_domain = _get_input(f'Enter host name for web application: [app.{domain}]: ', default='app.' + domain)

    # get the API subdomain value
    while not api_domain.endswith(domain):
        api_domain = _get_input(f'Enter host name for REST API: [api.{domain}]: ', default='api.' + domain)

    # get the websocket subdomain value
    while not ws_domain.endswith(domain):
        ws_domain = _get_input(f'Enter host name for websocket API: [ws.{domain}]: ', default='ws.' + domain)

    return hosted_zone_id, domain, app_domain, api_domain, ws_domain


def _setup_get_admin_data() -> (str, str, str):
    """
    Ask the user to enter administrator data
    :return: User entered administrator data
    """
    # get the admin user's full name
    full_name: str = _get_input('Enter administrator\'s full name: ')

    # get the admin user's email address
    email: str = _get_input('Enter email address for application administrator: ')

    # get the admin user's password
    password: str = _get_input('Enter administrator\'s new password: ', secret=True)

    return full_name, email, password


def _get_input(prompt: str, **kwargs) -> str:
    """
    Get user input from stdin
    :param prompt: User prompt
    :param kwargs: (min, max) for integer input; options for string input
    :return: User input
    """
    # get the user input
    if 'secret' in kwargs and kwargs['secret']:
        user_input: str = getpass.getpass(prompt)
    else:
        user_input: str = input(prompt).strip()

    # return the default value if provided
    if user_input == '' and 'default' in kwargs:
        return kwargs['default']

    # validate the input
    valid: bool = False
    if 'min' in kwargs and 'max' in kwargs:
        try:
            user_input_num = int(user_input.strip())
            if user_input_num < kwargs['min'] or user_input_num > kwargs['max']:
                raise ValueError
            return str(user_input_num)
        except ValueError:
            print('Invalid selection. Enter a number between ' + str(kwargs['min']) + ' and ' + str(kwargs['max']))

    # check for valid option
    elif 'options' in kwargs:
        valid = user_input in kwargs['options']

    # no validation methods provided
    else:
        return user_input

    # invalid input, try again
    if not valid:
        return _get_input(prompt, **kwargs)


def _get_available_domains() -> List[dict]:
    """
    Get a list of available hosted zones
    :return: List of hosted zone information
    """
    # query available hosted zones in the account
    session = get_aws_session()
    route53 = session.client('route53')
    res = route53.list_hosted_zones()

    # check response for error message
    if res['ResponseMetadata']['HTTPStatusCode'] != 200:
        print('Failed to query list of Route 53 hosted zones')
        return []

    return res['HostedZones']


def _add_email_identity(email: str) -> bool:
    """
    Create a new email sender identity
    :param email: Email address to verify
    :return: True if identity added (not confirmed)
    """
    # get an SES client
    session = get_aws_session()
    ses = session.client('sesv2')

    # send email confirmation
    res = ses.create_email_identity(EmailIdentity=email)

    # check the status
    if res['ResponseMetadata']['HTTPStatusCode'] != 200:
        print('Failed to add email sender identity.')
        return False
    return True


def _wait_for_email_identity_confirmation(email: str) -> None:
    """
    Wait for user to confirm the email sender identity
    :param email: Wait for this sender identity to be confirmed
    """
    # get an SES client
    session = get_aws_session()
    ses = session.client('sesv2')

    # send email confirmation
    res = ses.get_email_identity(EmailIdentity=email)
    if not res['VerifiedForSendingStatus']:
        print(f'Please check your email {email} and click the link to confirm.')
        sleep(2)
        _wait_for_email_identity_confirmation(email)


class WrfCloudCertificates(CloudFormation):
    """
    Help manipulate the CloudFormation stack that contains the web certificates
    """
    def __init__(self, hosted_zone_id: str):
        """
        AWS requires these resources to be created in us-east-1
        """
        self.acm_client = None
        self.r53_client = None
        self.hosted_zone_id = hosted_zone_id
        super().__init__(region='us-east-1')

    def _get_acm_client(self) -> any:
        """
        Get the ACM (Amazon Certificate Manager) client
        """
        if not self.acm_client:
            session = get_aws_session(region=self.region)
            self.acm_client = session.client('acm')
        return self.acm_client

    def _get_route53_client(self) -> any:
        """
        Get the ACM (Amazon Certificate Manager) client
        """
        if not self.r53_client:
            session = get_aws_session(region=self.region)
            self.r53_client = session.client('route53')
        return self.r53_client

    def validate_certificates(self):
        """
        Validate the certificates in the stack with the DNS method
        """
        sleep(20)

        # get the certificate ARN
        certificate_arn: Union[str, None] = None
        while certificate_arn is None:
            try:
                certificate_arn = self.get_stack_resource(logical='Certificate')
                sleep(1)
            except Exception as ignore:
                pass
        print(f'Found certificate: {certificate_arn}')

        # describe the certificate
        acm = self._get_acm_client()
        res = acm.describe_certificate(CertificateArn=certificate_arn)
        validations = res['Certificate']['DomainValidationOptions']

        # create a list of record set changes
        changes = []
        for validation in validations:
            if validation['ValidationStatus'] == 'PENDING_VALIDATION':
                record = validation['ResourceRecord']
                name = record['Name']
                value = record['Value']
                print(f'Adding record set: {name} -> {value}')
                changes.append(
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': name,
                            'Type': 'CNAME',
                            'TTL': 60,
                            'ResourceRecords': [
                                {
                                    'Value': value
                                }
                            ]
                        }
                    }
                )

        # add record sets to route53 to validate the certificates
        r53 = self._get_route53_client()
        res = r53.change_resource_record_sets(
            HostedZoneId=self.hosted_zone_id,
            ChangeBatch={
                'Comment': 'wrfcloud certificates',
                'Changes': changes
            }
        )

        return res['ResponseMetadata']['HTTPStatusCode'] == 200


if __name__ == '__main__':
    setup()
