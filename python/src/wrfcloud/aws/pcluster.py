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
from pcluster.cli.entrypoint import run as pcluster
from wrfcloud.log import Logger
from wrfcloud.system import init_environment, get_aws_session


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
        self.log = Logger(WrfCloudCluster.__class__.__name__)
        self.cluster_name = cluster_name or os.environ['USER']
        self.region = region or get_aws_session().region_name
        self.profile = profile or 'wrfcloud'
        self.subnet = subnet or self._get_default_subnet_id()
        self.ami = ami or self._get_latest_ami_id()
        self.cluster_config = cluster_config or 'aws/resources/cluster.wrfcloud.yaml'
        self.cf_client = None

    def create_cluster(self, custom_action: str = None) -> None:
        """
        Create a cluster using AWS ParallelCluster
        :param custom_action: Command line to run when cluster is configured and ready
        """
        # create the configuration file data
        data = pkgutil.get_data('wrfcloud', self.cluster_config).decode()
        data = data.replace('__USER__', os.environ['USER'])
        data = data.replace('__SUBNET_ID__', self.subnet)
        data = data.replace('__AMI_ID__', self.ami)
        data = data.replace('__REGION__', self.region)

        # maybe add the custom action to the configuration
        if custom_action:
            data = self._add_custom_action_to_config(custom_action, data)

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
        self._wait_for_stack_status('CREATE_COMPLETE')

        # delete the temporary file
        os.unlink(config_file)

    def update_cluster(self):
        """
        Use pcluster to update an existing cluster for the current user
        """
        status = self._get_stack_status()
        if status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            print(f'Cluster {self.cluster_name} is not ready for an update. Check its status.')
            return

        # create the configuration file data
        data = pkgutil.get_data('wrfcloud', self.cluster_config).decode()
        data = data.replace('__USER__', os.environ['USER'])
        data = data.replace('__SUBNET_ID__', self.subnet)
        data = data.replace('__AMI_ID__', self.ami)
        data = data.replace('__REGION__', self.region)

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

    def delete_cluster(self):
        """
        Use pcluster to stop the current user's cluster
        """
        status = self._get_stack_status()
        if status is None or status == '':
            print(f'Cluster {self.cluster_name} is not running.')
            return

        params = f'delete-cluster --region {self.region} --cluster-name {self.cluster_name}'.split()
        ret = pcluster(params)
        if ret:
            output_str = json.dumps(ret, indent=2)
            print(output_str)

        # wait for the stack status
        self._wait_for_stack_status(None)

    def cluster_status(self):
        """
        Print the cluster status
        """
        self._print_status_message()

    def connect_cluster(self):
        """
        Connect to the cluster via SSH
        """
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

    @staticmethod
    def _add_custom_action_to_config(custom_action: str, data: str) -> str:
        """
        Add a custom action to the configuration
        :param custom_action: Run this command on configure complete
        :param data: ParallelCluster configuration data
        """
        # make sure there is a custom action
        if custom_action is None or custom_action.strip() == '':
            return data

        # load the configuration data into a dictionary
        config = yaml.safe_load(data)

        # split the custom action into a script and arguments
        parts = custom_action.split()
        script = parts[0]
        args = parts[1:] if len(parts) > 1 else None

        # create a custom action section of the configuration file
        custom_action_section = {'OnNodeConfigured': {'Script': script}}
        if args:
            custom_action_section['OnNodeConfigured']['Args'] = args

        # insert the custom action section into the document
        config['HeadNode']['CustomActions'] = custom_action_section
        print(config['HeadNode']['CustomActions'])
        return yaml.dump(config, indent=2)

    def _confirm_ssh_config(self, data: str) -> str:
        """
        Confirm the SSH configuration will work
        :param data: ParallelCluster configuration data
        :return: Updated ParallelCluster configuration data with SSH confirmation
        """
        # get the current user
        user = os.environ['USER']

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
        latest_image = None
        for image in images:
            if image['Name'].startswith('wrf-4-4-0'):
                if latest_image is None:
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


def _print_usage_and_exit() -> None:
    """
    Prints the script usage and exits
    """
    print('Script to help start up the WRF Cloud Cluster with ParallelCluster')
    print('Usage:')
    print(f'   {sys.argv[0]} <status|create|delete|update|connect|dashboard>')
    sys.exit(0)


def main() -> None:
    """
    Command line interface main function -- use as entrypoint
    """
    # initialize the production environment
    init_environment('production')

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
    image_builder = WrfCloudCluster(cluster_name=args.name)

    # run specified command
    if command == 'delete':
        image_builder.delete_cluster()
    elif command == 'create':
        image_builder.create_cluster(custom_action=args.command)
    elif command == 'update':
        image_builder.update_cluster()
    elif command == 'status':
        image_builder.cluster_status()
    elif command == 'connect':
        image_builder.connect_cluster()
    elif command == 'dashboard':
        image_builder.open_dashboard()
    else:
        _print_usage_and_exit()
