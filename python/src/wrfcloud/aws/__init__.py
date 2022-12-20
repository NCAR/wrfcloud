"""
AWS functions for WRF Cloud
"""
import pkgutil
from typing import Union
from datetime import datetime
import time
import botocore.exceptions
from wrfcloud.system import get_aws_session

__all__ = ['imagebuilder', 'pcluster', 'CloudFormation']


class CloudFormation:
    """
    Class to help out with CloudFormation operations
    """
    def __init__(self, region: Union[str, None] = None):
        """
        Set default values
        :param region: Override the AWS region to manipulate the CF stack
        """
        self.region = region
        self.stack_id: str = ''
        self.stack_name: str = ''
        self.cf_template_resource: str = ''
        self.cf_client = None
        self.parameters = []

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
        res = cloudformation.create_stack(
            StackName=self.stack_name,
            TemplateBody=template_body,
            Capabilities=['CAPABILITY_IAM'],
            Parameters=self.parameters
        )

        # get the stack ID from the response if there is one
        self.stack_id = res['StackId'] if 'StackId' in res else None

        # monitor the stack status until creation is complete
        self._wait_for_stack_status('CREATE_COMPLETE')

    def get_stack_resource(self, logical: str = None) -> str:
        """
        Get the ARN of the given resource
        :param logical: The logical resource name
        :return: Resource ARN or None if not found
        """
        # get the cloudformation client
        cloudformation = self._get_cloudformation_client()

        # get resource ARN from a logical resource ID
        if logical is not None:
            res = cloudformation.describe_stack_resource(StackName=self.stack_name, LogicalResourceId=logical)
            return res['StackResourceDetail']['PhysicalResourceId']

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

    def stack_status(self) -> None:
        """
        Print the stack status
        """
        self._print_status_message()

    def _get_cloudformation_client(self) -> any:
        """
        Get the AWS client object for the CloudFormation service
        """
        if not self.cf_client:
            session = get_aws_session(region=self.region)
            self.cf_client = session.client('cloudformation')
        return self.cf_client

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
