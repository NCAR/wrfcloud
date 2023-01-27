"""
This is the command line interface to simplify running the ImageBuilder steps
"""

import os
import sys
import botocore.exceptions
from wrfcloud.system import init_environment, get_aws_session
from wrfcloud.aws import CloudFormation


class WrfCloudImageBuilder(CloudFormation):
    """
    Class to start the Image Builder stack
    """
    def __init__(self, stack_name: str = None, cf_file: str = None, image_name: str = None, region: str = None):
        """
        Initialize parameters
        """
        super().__init__(region)
        self.stack_name = stack_name or 'WrfIntelImageBuilder'
        self.cf_template_resource = cf_file or 'aws/resources/cf_imagebuilder_wrf_intel.yaml'
        self.image_name = image_name or 'wrf-4-4-0'
        self.stack_id = None
        self.cf_client = None
        self.ib_client = None
        self.ec2_client = None

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
