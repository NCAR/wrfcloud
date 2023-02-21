"""
This is the command line interface to simplify running the ParallelCluster steps
"""

from typing import Union
import os
import sys
import json
import pkgutil
import tempfile
import time
import yaml
from datetime import datetime
from wrfcloud.log import Logger
from wrfcloud.system import init_environment, get_aws_session


class CustomAction:
    """
    Represents a custom action to run on the cluster
    """
    def __init__(self, ref_id: str, script_contents: str, bucket_name: str = None,
                 object_prefix: str = None, object_name: str = None):
        """
        Initialize the custom action
        """
        self.log = Logger(self.__class__.__name__)
        self.ref_id = ref_id
        self.script_contents = script_contents
        self.bucket_name = bucket_name if bucket_name is not None else os.environ['WRFCLOUD_BUCKET']
        self.object_prefix = object_prefix if object_prefix is not None else f'CustomAction/{ref_id}'
        self.object_name = object_name if object_name is not None else 'on_configure.sh'

    @property
    def s3_url(self):
        """
        Get the S3 URL
        """
        return f's3://{self.bucket_name}/{self.s3_key}'

    @property
    def s3_key(self):
        """
        Get the S3 key
        """
        return f'{self.object_prefix}/{self.object_name}'

    def upload(self) -> bool:
        """
        Upload the custom action script to S3
        """
        # upload the script to S3
        session = get_aws_session()
        s3 = session.client('s3')
        res = s3.put_object(
            Body=self.script_contents.encode(),
            Bucket=self.bucket_name,
            Key=self.s3_key
        )

        # check the status of uploading the object to S3
        if res['ResponseMetadata']['HTTPStatusCode'] != 200:
            self.log.error(f'Failed to upload custom action to S3: {self.s3_url}')
            return False
        return True


class WrfCloudCluster:
    """
    Class to start the WRF Cloud cluster via AWS ParallelCluster
    """

    def __init__(self, cluster_name: str = None, region: str = None, profile: str = None,
                 subnet: str = None, ami: str = None, cluster_config: str = None):
        """
        Initialize parameters
        :param cluster_name: Cluster name for the CF stack or None for default value
        :param region: Region in which to run the cluster or None for default value
        :param profile: AWS profile to start the cluster or None for default value
        :param subnet: Subnet ID in which to place the cluster or None for default value
        :param ami: AMI ID to use for the cluster nodes or None for default value
        :param cluster_config: Path to cluster configuration
        """
        user = os.environ['USER'] if 'USER' in os.environ else 'wrfcloud-admin'
        self.log = Logger(WrfCloudCluster.__class__.__name__)
        self.cluster_name = cluster_name or user
        self.region = region or get_aws_session().region_name
        self.profile = profile or 'wrfcloud'
        self.subnet = subnet or self._get_default_subnet_id()
        self.ami = ami or self._get_latest_ami_id()
        self.cluster_config = cluster_config or 'aws/resources/cluster.wrfcloud.yaml'
        self.cf_client = None
        self.ssh_cidr_ip_range: Union[str, None] = None

    def print_summary(self) -> None:
        """
        Print a summary of options
        """
        self.log.info(f'Cluster Name: {self.cluster_name}')
        self.log.info(f'AWS Region: {self.region}')
        self.log.info(f'Profile: {self.profile}')
        self.log.info(f'Subnet ID: {self.subnet}')
        self.log.info(f'AMI ID: {self.ami}')
        self.log.info(f'SSH Access: {self.ssh_cidr_ip_range}')

    def set_ssh_security_group_ip(self, cidr_ip_range: str) -> None:
        """
        Set the CIDR block that can connect to the head node via SSH
        :param cidr_ip_range: IP address range in CIDR notation
        """
        self.ssh_cidr_ip_range = cidr_ip_range

    def create_cluster(self, custom_action: CustomAction = None, wait: bool = True) -> None:
        """
        Create a cluster using AWS ParallelCluster
        :param custom_action: Script contents to run when cluster is configured and ready
        :param wait: Do not return until the stack status is CREATE_COMPLETE
        """
        # slow import deferred
        from pcluster.cli.entrypoint import run as pcluster

        # get this AWS account ID
        account_id: str = self._get_aws_account_id()

        # create the configuration file data
        user = os.environ['USER'] if 'USER' in os.environ else 'wrfcloud-admin'
        data = pkgutil.get_data('wrfcloud', self.cluster_config).decode()
        data = data.replace('__USER__', user)
        data = data.replace('__SUBNET_ID__', self.subnet)
        data = data.replace('__AMI_ID__', self.ami)
        data = data.replace('__REGION__', self.region)
        data = data.replace('__AWS_ACCOUNT_ID__', account_id)

        # maybe add the custom action to the configuration
        if custom_action:
            data = self._setup_custom_action(custom_action, data)

        # maybe remove the SSH configuration
        data = self._confirm_ssh_config(data)

        # write the configuration file
        config_file = tempfile.mkstemp()[1]
        with open(config_file, 'w') as file_out:
            file_out.write(data)
            file_out.close()

        # create the command line parameters and run
        params = f'create-cluster --region {self.region} --cluster-name {self.cluster_name} ' \
                 f'--cluster-configuration {config_file}'.split()
        ret = pcluster(params)
        if ret:
            output_str = json.dumps(ret, indent=2)
            print(output_str)

        # wait for the stack status
        if wait:
            self._wait_for_stack_status('CREATE_COMPLETE')

        # delete the temporary file
        os.unlink(config_file)

    def update_cluster(self):
        """
        Use pcluster to update an existing cluster for the current user
        """
        # slow import deferred
        from pcluster.cli.entrypoint import run as pcluster

        status = self._get_stack_status()
        if status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            print(f'Cluster {self.cluster_name} is not ready for an update. Check its status.')
            return

        # get the account ID
        account_id = self._get_aws_account_id()

        # create the configuration file data
        user = os.environ['USER'] if 'USER' in os.environ else 'wrfcloud-admin'
        data = pkgutil.get_data('wrfcloud', self.cluster_config).decode()
        data = data.replace('__USER__', user)
        data = data.replace('__SUBNET_ID__', self.subnet)
        data = data.replace('__AMI_ID__', self.ami)
        data = data.replace('__REGION__', self.region)
        data = data.replace('__AWS_ACCOUNT_ID__', account_id)

        # write the configuration file
        config_file = tempfile.mkstemp()[1]
        with open(config_file, 'w') as file_out:
            file_out.write(data)
            file_out.close()

        params = f'update-cluster --region {self.region} --cluster-name {self.cluster_name} ' \
                 f'--cluster-configuration {config_file}'.split()
        ret = pcluster(params)
        if ret:
            output_str = json.dumps(ret, indent=2)
            print(output_str)

        # wait for the stack status
        self._wait_for_stack_status('UPDATE_COMPLETE')

        # delete the temporary file
        os.unlink(config_file)

    def delete_cluster(self, wait: bool = True) -> bool:
        """
        Use pcluster to stop the current user's cluster
        :param wait: Do not return until cluster is fully deleted
        :return: True if successful, otherwise False
        """
        # slow import deferred
        from pcluster.cli.entrypoint import run as pcluster

        status = self._get_stack_status()
        if status is None or status == '':
            print(f'Cluster {self.cluster_name} is not running.')
            return

        ok: bool = False
        params = f'delete-cluster --region {self.region} --cluster-name {self.cluster_name}'.split()
        ret = pcluster(params)
        if ret:
            ok = True
            output_str = json.dumps(ret, indent=2)
            print(output_str)

        # wait for the stack status
        if wait:
            self._wait_for_stack_status(None)

        return ok

    def cluster_status(self):
        """
        Print the cluster status
        """
        self._print_status_message()

    def connect_cluster(self):
        """
        Connect to the cluster via SSH
        """
        # slow import deferred
        from pcluster.cli.entrypoint import run as pcluster

        # check if the cluster exists
        status = self._print_status_message()
        if status is None or status == '':
            print(f'Cluster {self.cluster_name} is not running.')
            return

        # connect to the cluster
        params = f'ssh --region {self.region} --cluster-name {self.cluster_name}'.split()
        pcluster(params)

    def open_dashboard(self):
        """
        Open the cluster dashboard in the AWS console
        """
        url = f'https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}' \
              f'#dashboards:name={self.cluster_name}-{self.region}'
        print(f'Dashboard at:  {url}')

    def _setup_custom_action(self, custom_action: CustomAction, data: str) -> str:
        """
        Add a custom action to the configuration
        :param custom_action: Script contents which will be run on the cluster head node
        :param data: ParallelCluster configuration data
        """
        # make sure there is a custom action
        if custom_action is None:
            return data
        if custom_action.script_contents is None or custom_action.script_contents.strip() == '':
            return data

        # load the configuration data into a dictionary
        config = yaml.safe_load(data)

        # create a custom action section of the configuration file
        custom_action_section = {'OnNodeConfigured': {'Script': custom_action.s3_url}}

        # insert the custom action section into the document
        config['HeadNode']['CustomActions'] = custom_action_section
        data = yaml.dump(config, indent=2)

        # upload the script to s3
        if not custom_action.upload():
            self.log.error(f'Failed to upload custom action script to S3: {custom_action.s3_url}')
            return ''

        return data

    def _confirm_ssh_config(self, data: str) -> str:
        """
        Confirm the SSH configuration will work
        :param data: ParallelCluster configuration data
        :return: Updated ParallelCluster configuration data with SSH confirmation
        """
        # get the current user
        user = os.environ['USER'] if 'USER' in os.environ else 'wrfcloud-admin'

        # check for the named ssh key in the account
        session = get_aws_session()
        ec2 = session.client('ec2')
        found = False
        try:
            res = ec2.describe_key_pairs(KeyNames=[user])
            if res['ResponseMetadata']['HTTPStatusCode'] == 200:
                if res['KeyPairs'][0]['KeyName'] == user:
                    found = True
        except Exception as ignore:
            if ignore.__class__.__name__ != 'ClientError':
                self.log.error(f'Failed to check for named SSH key: {user}')

        # remove the SSH configuration from the configuration if the key is not found
        if not found:
            config = yaml.safe_load(data)
            config['HeadNode'].pop('Ssh')
            data = yaml.dump(config, indent=2)

        # add an IP range that can connect via SSH if provided
        elif self.ssh_cidr_ip_range is not None:
            config = yaml.safe_load(data)
            config['HeadNode']['Ssh']['AllowedIps'] = self.ssh_cidr_ip_range
            data = yaml.dump(config, indent=2)

        return data

    def _get_stack_status(self) -> Union[str, None]:
        """
        Make an API call to get the stack status.  Sets the 'status' variable before return.
        """
        try:
            cloudformation = self._get_cloudformation_client()
            res = cloudformation.describe_stacks(StackName=self.cluster_name)

            # return None if stack is not found
            if len(res['Stacks']) == 0:
                return None

            # return the stack status
            return res['Stacks'][0]['StackStatus']
        except Exception:
            return None

    def _print_status_message(self) -> str:
        """
        Print the current stack status
        :return: The stack status
        """
        status = self._get_stack_status()
        s1 = status or '<stack does not exist>'
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{self.cluster_name} ... {s1} ... {dt}')
        return status

    def _wait_for_stack_status(self, target_status: Union[str, None]):
        """
        Monitor the stack status until creation is complete
        :param target_status: Do not return until this status is reached
        """
        status = self._print_status_message()

        while status != target_status:
            time.sleep(2)
            status = self._print_status_message()

    def _get_cloudformation_client(self) -> any:
        """
        Get the AWS client object for the CloudFormation service
        """
        if not self.cf_client:
            session = get_aws_session()
            self.cf_client = session.client('cloudformation')
        return self.cf_client

    def _get_latest_ami_id(self) -> Union[None, str]:
        """
        Get the latest WRF AMI ID
        :return: Latest AMI ID, or None if no images exist or lacking permissions
        """
        # get an AWS session from the wrfcloud environment
        session = get_aws_session()

        # get our account ID
        sts = session.client('sts')
        res = sts.get_caller_identity()
        if res['ResponseMetadata']['HTTPStatusCode'] != 200:
            self.log.error('Failed to get AWS account ID through STS')
            return None
        account_id = res['Account']

        # get a list of image descriptions for our account
        ec2 = session.client('ec2')
        res = ec2.describe_images(Owners=[account_id])
        if res['ResponseMetadata']['HTTPStatusCode'] != 200:
            return None
        images = res['Images']
        latest_image: dict = {}
        for image in images:
            if image['Name'].startswith('wrf-4-4-0'):
                if not latest_image:
                    latest_image = image
                elif image['CreationDate'] > latest_image['CreationDate']:
                    latest_image = image

        return latest_image['ImageId']

    def _get_default_subnet_id(self) -> Union[None, str]:
        """
        Get the default subnet ID for the cluster
        :return: Subnet ID
        """
        # get an EC2 client to query available subnets
        session = get_aws_session()
        ec2 = session.client('ec2')

        # query subnets and make sure we get a valid response
        res = ec2.describe_subnets()
        if res['ResponseMetadata']['HTTPStatusCode'] != 200:
            self.log.warn('Unable to get default subnet ID')
            return None

        # query subnets
        for subnet in res['Subnets']:
            if subnet['AvailabilityZoneId'].endswith('-az2'):
                return subnet['SubnetId']

        # did not find a match
        return None

    def _get_aws_account_id(self) -> str:
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
            self.log.warn('Unable to get AWS account ID')
            return '000000000000'
        return res['Account']


def _print_usage_and_exit() -> None:
    """
    Prints the script usage and exits
    """
    print('Script to help start up the WRF Cloud Cluster with ParallelCluster')
    print('Usage:')
    print(f'   {sys.argv[0]} <status|create|delete|update|connect|dashboard>')
    sys.exit(0)


def _build_custom_action(ref_id: str, command: str) -> Union[CustomAction, None]:
    """
    Build a custom action from the command line parameter
    :param ref_id: Reference ID, typically using the cluster name
    :param command: Command to run on the cluster
    :return: Custom Action object, or None if no command is given
    """
    # return None if no command is given
    if command is None:
        return None

    # return a CustomAction object
    script = f'#! /bin/bash\n\n{command}\n'  # wrap the command in a bash script
    return CustomAction(ref_id=ref_id, script_contents=script)


def main() -> None:
    """
    Command line interface main function -- use as entrypoint
    """
    # initialize the cli environment
    init_environment('cli')

    # library to parse command line parameters
    from argparse import ArgumentParser

    # check the command line parameter usage
    if len(sys.argv) < 2:
        _print_usage_and_exit()

    # get the command
    command = sys.argv[1]

    # build the argument parser
    parser = ArgumentParser(description='Control a WRF cluster')
    parser.add_argument('--name', type=str, help='Cluster name or unique ID', required=False, default=None)
    if command == 'create':
        parser.add_argument('--command', type=str, help='Command to run on the cluster', required=False, default=None)
    args = parser.parse_args(sys.argv[2:])

    # get a WrfCloudCluster instance
    cluster = WrfCloudCluster(cluster_name=args.name)

    # run specified command
    if command == 'delete':
        cluster.delete_cluster()
    elif command == 'create':
        ca = _build_custom_action(cluster.cluster_name, args.command)
        cluster.create_cluster(custom_action=ca)
    elif command == 'update':
        cluster.update_cluster()
    elif command == 'status':
        cluster.cluster_status()
    elif command == 'connect':
        cluster.connect_cluster()
    elif command == 'dashboard':
        cluster.open_dashboard()
    else:
        _print_usage_and_exit()
