__all__ = ['aws', 'setup']

import os
import pkgutil
import mimetypes
import getpass
import hashlib
import random
import base64
import glob
import secrets
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from typing import List, Union
import yaml
from wrfcloud.config import WrfConfig
from wrfcloud.config import add_config_to_system
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
    s3_bucket = _create_s3_bucket_name()

    # Collect input parameters - custom domain names (app, api, ws); admin email/password
    _setup_get_user_data(user_data)

    # Enable SES identity
    print('Verify email identity to allow sending email on your behalf...')
    _add_email_identity(user_data['admin_email'])
    _wait_for_email_identity_confirmation(user_data['admin_email'])

    # Create an additional policy for the WRF cluster
    _create_cluster_policy()

    # Image Builder - create stack and run image builder pipeline
    print('Creating WRF Image...')
    image_builder = WrfCloudImageBuilder()
    image_builder.replace_stack()
    image_builder.build_image()

    # CloudFormation - Data stack
    print('Creating CloudFormation Data Stack...')
    data_stack = CloudFormation()
    data_stack.stack_name = 'WrfCloudApiData'
    data_stack.cf_template_resource = 'setup/aws/cf_wrfcloud_data.yaml'
    data_stack.parameters.append({'ParameterKey': 'AppName', 'ParameterValue': 'wrfcloud'})
    data_stack.parameters.append({'ParameterKey': 'DeploymentType', 'ParameterValue': 'production'})
    data_stack.parameters.append({'ParameterKey': 'WrfCloudBucket', 'ParameterValue': s3_bucket})
    data_stack.create_stack()

    # Upload public key
    if 'ssh_key' in user_data:
        print('Uploading public SSH key to AWS...')
        _upload_public_ssh_key(user_data['ssh_key'])

    # Deploy build artifacts (lambda layer, function, web app)
    print(f'Uploading build artifacts to S3 bucket ({s3_bucket}) ...')
    _upload_to_s3(s3_bucket, 'artifacts/lambda_layer.zip', 'lambda_layer.zip', 'Enter the location of the lambda layer zip file: ')
    _upload_to_s3(s3_bucket, 'artifacts/lambda_function.zip', 'lambda_function.zip', 'Enter the location of the lambda function zip file: ')
    _finalize_and_upload_webapp_to_s3(s3_bucket, 'web', 'web', 'Enter the location of the Angular web application build: ', user_data['api_domain'], user_data['ws_domain'])

    # CloudFormation - Certificate stack - DNS certificate verification
    print('Creating CloudFormation Web Certificate Stack...')
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
    print('Creating CloudFormation Web Application Stack...')
    jwt_signing_key = secrets.token_hex(64)
    webapp_stack = CloudFormation()
    webapp_stack.stack_name = 'WrfCloudWebApp'
    webapp_stack.cf_template_resource = 'setup/aws/cf_wrfcloud_webapp.yaml'
    webapp_stack.parameters.append({'ParameterKey': 'AdminUserEmail', 'ParameterValue': user_data['admin_email']})
    webapp_stack.parameters.append({'ParameterKey': 'AppName', 'ParameterValue': 'wrfcloud'})
    webapp_stack.parameters.append({'ParameterKey': 'DeploymentType', 'ParameterValue': 'production'})
    webapp_stack.parameters.append({'ParameterKey': 'DomainName', 'ParameterValue': user_data['domain']})
    webapp_stack.parameters.append({'ParameterKey': 'WebHostName', 'ParameterValue': user_data['app_domain']})
    webapp_stack.parameters.append({'ParameterKey': 'ApiHostName', 'ParameterValue': user_data['api_domain']})
    webapp_stack.parameters.append({'ParameterKey': 'WebsocketHostName', 'ParameterValue': user_data['ws_domain']})
    webapp_stack.parameters.append({'ParameterKey': 'JwtSigningKey', 'ParameterValue': jwt_signing_key})
    webapp_stack.parameters.append({'ParameterKey': 'StageName', 'ParameterValue': 'v1'})
    webapp_stack.parameters.append({'ParameterKey': 'HostedZoneId', 'ParameterValue': user_data['hosted_zone_id']})
    webapp_stack.parameters.append({'ParameterKey': 'CertificateArn', 'ParameterValue': certificate_stack.certificate_arn})
    webapp_stack.parameters.append({'ParameterKey': 'WrfCloudBucket', 'ParameterValue': s3_bucket})
    webapp_stack.create_stack()

    # Create admin user
    print('Creating admin user in WRF Cloud...')
    admin = User()
    admin.full_name = user_data['full_name']
    admin.email = user_data['admin_email']
    admin.password = user_data['admin_password']
    admin.role_id = 'admin'
    admin.active = True
    add_user_to_system(admin)

    # Installing example data
    if user_data['include_examples']:
        print('Installing sample data...')
        _install_sample_data(s3_bucket)

    # Complete confirmation
    print('----------------------------------------------------------')
    print('WRF Cloud installation is complete.')
    print('Open your browser to https://' + user_data['app_domain'])
    print('----------------------------------------------------------')


def _create_s3_bucket_name() -> str:
    """
    Get the S3 bucket name
    """
    # make one up
    sha = hashlib.sha256()
    for i in range(10):
        sha.update(str(random.random()).encode())
    suffix = base64.b16encode(sha.digest()).decode()[0:8].lower()
    s3_bucket = 'wrfcloud-' + suffix
    return s3_bucket


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

    # get option to install example model configurations
    include_examples = _setup_yes_no('Do you want to install example model configurations (yes/no)? ')
    user_data['include_examples'] = include_examples

    # get SSH public key for admin user
    add_ssh = _setup_yes_no('Do you want to upload an SSH public key for an admin?  Without it, you cannot access your clusters to debug. (yes/no)? ')
    if add_ssh:
        user_data['ssh_key'] = _get_input('Paste your public key, often found at ${HOME}/.ssh/id_rsa.pub: ')

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
        print(str(i + 1) + '. ' + domains[i]['Name'])
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


def _setup_yes_no(prompt: str) -> bool:
    """
    Ask a yes/no question
    :return: True=yes, False=no
    """
    answer: str = _get_input(f'{prompt} ', options=['yes', 'y', 'no', 'n', 'Y', 'N'])
    return answer[0].upper() == 'Y'


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
    return user_input


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

    # delete the email identity if it already exists AND is not verified
    try:
        res = ses.get_email_identity(EmailIdentity=email)
        if res['VerificationStatus'] == 'SUCCESS':
            return True
        ses.delete_email_identity(EmailIdentity=email)
    except Exception:
        pass

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


def _upload_to_s3(bucket: str, key: str, default_file: str, not_found_prompt: Union[str, None]) -> None:
    """
    Upload the lambda function to the S3 bucket
    :param bucket: S3 bucket name
    :param key: S3 key
    :param default_file: Check for this file first
    :param not_found_prompt: User prompt if file is not found
    :return: None
    """
    # ask for the lambda layer zip file location if not found
    while not os.path.isfile(default_file) and not_found_prompt is not None:
        default_file = _get_input(not_found_prompt, default=default_file)

    # upload the zip file as lambda layer
    try:
        print(f'Uploading {default_file} to s3://{bucket}/{key} ...')
        s3 = get_aws_session().client('s3')
        s3.upload_file(Filename=default_file, Bucket=bucket, Key=key)
    except Exception as e:
        print(f'Failed to upload file: {default_file}')
        print(e)


def _finalize_and_upload_webapp_to_s3(bucket: str, prefix: str, default_dir: str, not_found_prompt: str, api: str,
                                      ws: str) -> None:
    """
    Sync the directory to the S3 bucket
    :param bucket: S3 bucket name
    :param prefix: S3 key
    :param default_dir: Check for this file first
    :param not_found_prompt: User prompt if file is not found
    :param api: API hostname
    :param ws: Websocket hostname
    :return: None
    """
    # ask for the lambda layer zip file location if not found
    while not os.path.isdir(default_dir):
        default_dir = _get_input(not_found_prompt, default=default_dir)

    # strip off trailing '/' characters
    while default_dir.endswith('/'):
        default_dir = default_dir[:-1]

    # get the files that need to be uploaded
    files = []
    for f in glob.iglob(f'{default_dir}/**/*', recursive=True):
        if os.path.isfile(f):
            files.append(f[len(default_dir) + 1:])

    # upload the zip file as lambda layer
    s3 = get_aws_session().client('s3')
    for file in files:
        try:
            file_with_path = f'{default_dir}/{file}'
            _search_and_replace(file_with_path, '__API_HOSTNAME__', api)
            _search_and_replace(file_with_path, '__WS_HOSTNAME__', ws)
            mime_type: str = _get_mime_type(file)
            print(f'Uploading {file} to s3://{bucket}/{prefix}/{file} as {mime_type} ...')
            s3.upload_file(
                Filename=f'{default_dir}/{file}',
                Bucket=bucket,
                Key=f'{prefix}/{file}',
                ExtraArgs={'ContentType': mime_type}
            )
        except Exception as e:
            print(f'Failed to upload file: {file}')
            print(e)


def _get_mime_type(file: str) -> str:
    """
    Get the MIME type of the file
    :param file: Get the MIME type of this file
    :return: The file's MIME type
    """
    # use the mimetypes library to guess the MIME type
    mime_type: str = mimetypes.guess_type(file)[0]

    # if the library fails, use the file extension or default
    if mime_type is None:
        extension: str = file[file.rfind('.') + 1:]
        extension_to_mime = {
            'js': 'application/javascript',
            'ttf': 'font/ttf',
            'jpg': 'image/jpg',
            'png': 'image/png',
            'css': 'text/css',
            'html': 'text/html',
            'txt': 'text/plain'
        }
        if extension in extension_to_mime:
            mime_type = extension_to_mime[extension]
        else:
            mime_type = 'text/html'

    return mime_type


def _search_and_replace(file: str, stub: str, value: str) -> None:
    """
    Search and replace text in a file
    :param file: The file in which to search and replace
    :param stub: The text string to replace
    :param value: The value to substitute
    :return: None
    """
    # make sure the file type is amenable to a text search and replace
    if not file.endswith('.html') and not file.endswith('.js') and \
            not file.endswith('.css') and not file.endswith('.txt'):
        return

    # read the file data
    with open(file, 'r') as in_file:
        data = in_file.read()
        in_file.close()

    # search and replace
    new_data = data.replace(stub, value)

    # write the file data
    with open(file, 'w') as out:
        out.write(new_data)
        out.close()


def _get_aws_account_id() -> str:
    """
    Get the AWS account ID
    :return: AWS account ID (12-digit string)
    """
    # get an STS client from the default session
    session = get_aws_session()
    sts = session.client('sts')

    # get the caller identify and return account ID
    res = sts.get_caller_identity()
    if res['ResponseMetadata']['HTTPStatusCode'] != 200:
        return '000000000000'
    return res['Account']


def _create_cluster_policy() -> None:
    """
    Create an additional policy passed to the cluster via ParallelCluster configuration
    """
    # get the aws account id
    account_id = _get_aws_account_id()

    # get the policy document
    policy_document: str = pkgutil.get_data('wrfcloud', 'setup/aws/wrfcloud_cluster_policy.json').decode()
    policy_document = policy_document.replace('__AWS_ACCOUNT_ID__', account_id)

    # set the policy name
    policy_name: str = 'wrfcloud_parallelcluster'

    # get an iam client
    iam = get_aws_session().client('iam')

    # delete the policy if it exists already
    try:
        policy_arn: str = f'arn:aws:iam::{account_id}:policy/{policy_name}'
        iam.delete_policy(PolicyArn=policy_arn)
    except Exception:
        pass

    # create the policy
    res = iam.create_policy(
        PolicyName='wrfcloud_parallelcluster',
        PolicyDocument=policy_document
    )

    if res['ResponseMetadata']['HTTPStatusCode'] != 200:
        print('Failed to create IAM policy: wrfcloud_parallelcluster')


def _delete_policy_if_exists() -> None:
    """
    Delete a policy if it exists in the account
    """


def _install_sample_data(s3_bucket: str) -> None:
    """
    Install sample data
    :param s3_bucket: Upload sample data to this S3 bucket
    :return: None
    """
    # make sure the bucket name is set in the environment
    if 'WRFCLOUD_BUCKET' not in os.environ:
        os.environ['WRFCLOUD_BUCKET'] = s3_bucket

    # load the sample configuration data from this package's resource
    config_data = yaml.safe_load(pkgutil.get_data('wrfcloud', 'setup/resources/caribbean_6km_config.yaml'))

    # create a WrfConfig object
    config: WrfConfig = WrfConfig(config_data)

    # save the configuration to the system
    try:
        ok = add_config_to_system(config)
    except Exception:
        ok = False

    # maybe write an error message
    if not ok:
        print('Failed to install sample model configuration.')


def _upload_public_ssh_key(pub_key: str) -> None:
    """
    Upload public key to AWS account
    :param pub_key: Public key material
    :return: None
    """
    try:
        ec2 = get_aws_session().client('ec2')
        res = ec2.import_key_pair(
            KeyName='wrfcloud-admin',
            PublicKeyMaterial=pub_key.encode()
        )
        if res['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise Exception('Failed to import SSH key')
    except Exception as e:
        print(
            'Failed to upload SSH key pair.  You can do this in the AWS console at https://us-east-2.console.aws.amazon.com/ec2/v2/home?region=us-east-2#KeyPairs:')
        print('Be sure to name the new key: wrfcloud-admin')


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
        self.certificate_arn = None
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
        self.certificate_arn: Union[str, None] = None
        while self.certificate_arn is None:
            try:
                self.certificate_arn = self.get_stack_resource(logical='Certificate')
                sleep(1)
            except Exception as ignore:
                pass
        print(f'Found certificate: {self.certificate_arn}')

        # describe the certificate
        acm = self._get_acm_client()
        res = acm.describe_certificate(CertificateArn=self.certificate_arn)
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
        if len(changes) > 0:
            r53 = self._get_route53_client()
            res = r53.change_resource_record_sets(
                HostedZoneId=self.hosted_zone_id,
                ChangeBatch={
                    'Comment': 'wrfcloud certificates',
                    'Changes': changes
                }
            )

            return res['ResponseMetadata']['HTTPStatusCode'] == 200
        return True
