"""
This is the command line interface to simplify running the ImageBuilder steps
"""

import pkgutil
from typing import Union
from datetime import datetime
import time
import os
import sys
import botocore.exceptions
from wrfcloud.system import init_environment, get_aws_session


class WrfCloudImageBuilder:
    """
    Class to start the Image Builder stack
    """

    def __init__(self, stack_name: str = None, cf_file: str = None, image_name: str = None,
                 region: str = None, profile: str = None):
        """
        Initialize parameters
        """
        self.stack_name = stack_name or 'WrfIntelImageBuilder'
        self.cf_template_resource = cf_file or 'aws/resources/cf_imagebuilder_wrf_intel.yaml'
        self.image_name = image_name or 'wrf-4-4-0'
        self.region = region or 'us-east-2'
        self.profile = profile or 'wrfcloud'
        self.stack_id = None
        self.cf_client = None
        self.ib_client = None
        self.ec2_client = None

    def create_stack(self) -> None:
        """
        Create the stack
        """
        # ensure that the stack does not already exist
        status = self._get_stack_status()
        if status is not None:
            print('Stack already exists, use replace or delete command.')
            return

        # create a new stack
        print('Creating stack...')

        # read the CloudFormation template
        template_body = pkgutil.get_data('wrfcloud', self.cf_template_resource).decode()

        # get cloudformation client
        cloudformation = self._get_cloudformation_client()
        res = cloudformation.create_stack(StackName=self.stack_name, TemplateBody=template_body, Capabilities=['CAPABILITY_IAM'])

        # get the stack ID from the response if there is one
        self.stack_id = res['StackId'] if 'StackId' in res else None

        # monitor the stack status until creation is complete
        self._wait_for_stack_status('CREATE_COMPLETE')

    def delete_stack(self) -> None:
        """
        Delete the stack
        """
        # get the current stack status
        status = self._get_stack_status()

        # nothing to do if it does not exist
        if not status or status == '':
            print('Stack does not exist.')
            return

        # delete the stack if not already in progress
        if status != 'DELETE_IN_PROGRESS':
            print('Deleting stack...')
            cloudformation = self._get_cloudformation_client()
            cloudformation.delete_stack(StackName=self.stack_name)

        # wait for stack to be gone
        self._wait_for_stack_status(None)

    def replace_stack(self) -> None:
        """
        Replace the stack (i.e., delete and create)
        """
        self.delete_stack()
        self.create_stack()

    def build_image(self) -> None:
        """
        Run the image pipeline to build the image
        """
        # get the imagebuilder client
        imagebuilder = self._get_imagebuilder_client()

        # get the pipeline ARN
        res1 = imagebuilder.list_image_pipelines(
            filters=[{'name': 'name', 'values': [self.image_name]}]
        )
        pipeline_arn = res1['imagePipelineList'][0]['arn'] if len(res1['imagePipelineList']) > 0 else None

        # start the pipeline build
        res2 = imagebuilder.start_image_pipeline_execution(imagePipelineArn=pipeline_arn)
        print(res2)

    def stack_status(self) -> None:
        """
        Print the stack status
        """
        self._print_status_message()

    def add_ssh_key(self) -> None:
        """
        Import the current user's public SSH key into EC2 service
        """
        # read the default SSH public key
        user = os.environ['USER']
        home = os.environ['HOME']
        pub_key = open(f'{home}/.ssh/id_rsa.pub').read().encode()

        # get the EC2 client
        ec2 = self._get_ec2_client()

        # import the public key
        try:
            res = ec2.import_key_pair(KeyName=user, PublicKeyMaterial=pub_key)
            print(res)
        except botocore.exceptions.ClientError as e:
            print(e)

    def _get_cloudformation_client(self) -> any:
        """
        Get the AWS client object for the CloudFormation service
        """
        if not self.cf_client:
            session = get_aws_session()
            self.cf_client = session.client('cloudformation')
        return self.cf_client

    def _get_imagebuilder_client(self) -> any:
        """
        Get the AWS client object for the ImageBuilder service
        """
        if not self.ib_client:
            session = get_aws_session()
            self.ib_client = session.client('imagebuilder')
        return self.ib_client

    def _get_ec2_client(self) -> any:
        """
        Get the AWS client object for the EC2 service
        """
        if not self.ec2_client:
            session = get_aws_session()
            self.ec2_client = session.client('ec2')
        return self.ec2_client

    def _print_status_message(self) -> str:
        """
        Print the current stack status
        :return: The stack status
        """
        status = self._get_stack_status()
        s1 = status or '<stack does not exist>'
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{self.stack_name} ... {s1} ... {dt}')
        return status

    def _get_stack_status(self) -> Union[str, None]:
        """
        Make an API call to get the stack status.  Sets the 'status' variable before return.
        """
        try:
            cloudformation = self._get_cloudformation_client()
            res = cloudformation.describe_stacks(StackName=self.stack_name)

            # return None if stack is not found
            if len(res['Stacks']) == 0:
                return None

            # return the stack status
            return res['Stacks'][0]['StackStatus']
        except botocore.exceptions.ClientError:
            return None

    def _wait_for_stack_status(self, target_status: Union[str, None]):
        """
        Monitor the stack status until creation is complete
        :param target_status: Do not return until this status is reached
        """
        status = self._print_status_message()

        while status != target_status:
            time.sleep(2)
            status = self._print_status_message()


def _print_usage_and_exit() -> None:
    """
    Prints the script usage and exits
    """
    print('Script to help manipulate the CloudFormation stack to build images.')
    print('Usage:')
    print(f'   {sys.argv[0]} <status|create|delete|replace|build|addkey>')
    exit(0)


def main() -> None:
    """
    Command line interface main function -- use as entrypoint
    """
    # initialize the production environment
    init_environment('production')

    # check the command line parameter usage
    if len(sys.argv) != 2:
        _print_usage_and_exit()

    # get the command
    command = sys.argv[1]

    # get an ImageBuilder object
    image_builder = WrfCloudImageBuilder()

    # run specified command
    if command == 'delete':
        image_builder.delete_stack()
    elif command == 'create':
        image_builder.create_stack()
    elif command == 'replace':
        image_builder.replace_stack()
    elif command == 'status':
        image_builder.stack_status()
    elif command == 'build':
        image_builder.build_image()
    elif command == 'addkey':
        image_builder.add_ssh_key()
    else:
        _print_usage_and_exit()
