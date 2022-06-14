from typing import Union
import os
import sys
import json
import pkgutil
import tempfile
import boto3
import time
from datetime import datetime
from pcluster.cli.entrypoint import run as pcluster


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
        self.cluster_name = cluster_name or os.environ['USER']
        self.region = region or 'us-east-2'
        self.profile = profile or 'wrfcloud'
        self.subnet = subnet or 'subnet-067bf9400b5ca5833'
        self.ami = ami or 'ami-05f10474df73ef152'
        self.cluster_config = cluster_config or 'aws/resources/cluster.wrfcloud.yaml'
        self.cf_client = None

    def create_cluster(self) -> None:
        """
        Create a cluster using AWS ParallelCluster
        """
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
            session = boto3.Session(region_name=self.region, profile_name=self.profile)
            self.cf_client = session.client('cloudformation')
        return self.cf_client

    def update_cluster(self):
        """
        Use pcluster to update an existing cluster for the current user
        """
        status = self._get_stack_status()
        if status != 'CREATE_COMPLETE' and status != 'UPDATE_COMPLETE':
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

        params = f'delete-cluster --region {self.region} --cluster-name {self.cluster_name}'.split
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


def _print_usage_and_exit() -> None:
    """
    Prints the script usage and exits
    """
    print('Script to help start up the WRF Cloud Cluster with ParallelCluster')
    print('Usage:')
    print(f'   {sys.argv[0]} <status|create|delete|update|connect|dashboard>')
    exit(0)


def main() -> None:
    """
    Command line interface main function -- use as entrypoint
    """
    # check the command line parameter usage
    if len(sys.argv) != 2:
        _print_usage_and_exit()

    # get the command
    command = sys.argv[1]

    # get an ImageBuilder object
    image_builder = WrfCloudCluster()

    # run specified command
    if command == 'delete':
        image_builder.delete_cluster()
    elif command == 'create':
        image_builder.create_cluster()
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
