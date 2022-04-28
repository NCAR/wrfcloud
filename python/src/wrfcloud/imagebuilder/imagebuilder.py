"""
Provide command line functions to operate on WRF ImageBuilder CloudFormation stacks
"""


import pkgutil
import time
from typing import List
from datetime import datetime
from argparse import ArgumentParser as ArgParse
from argparse import ArgumentDefaultsHelpFormatter as HelpFormatter
import boto3


def create_stack(stack_name: str) -> bool:
    """
    Create an ImageBuilder stack
    """
    # ensure that the stack does not already exist
    status = _get_stack_status(stack_name)
    if status != '':
        print(f'Stack already exists: {stack_name}')
        return False

    # load the template body
    template_body = pkgutil.get_data('imagebuilder', 'wrf/imagebuilder.yaml').decode()

    # create a new stack
    print(f"Creating stack {stack_name}...")
    client = boto3.client('cloudformation')
    client.create_stack(
        StackName=stack_name,
        Capabilities=['CAPABILITY_NAMED_IAM'],
        TemplateBody=template_body
    )

    # wait for stack create completion
    return _wait_for_status(stack_name, "CREATE_COMPLETE")


def replace_stack(stack_name: str) -> bool:
    """
    Delete and create the stack
    :stack_name: Stack name to replace
    :return: True if successful, otherwise False
    """
    # check the current status
    status = _get_stack_status(stack_name)

    # delete the stack if it already exists
    if status != '':
        if not delete_stack(stack_name):
            return False

    # create the stack
    return create_stack(stack_name)


def delete_stack(stack_name: str) -> bool:
    """
    Delete the CloudFormation stack
    :stack_name: Name of the CloudFormation stack to delete
    :return: True if successful, otherwise False
    """
    # get the current stack status
    status = _get_stack_status(stack_name)

    # nothing to do if it does not exist
    if status == '':
        print(f'Stack does not exist: {stack_name}')
        return False

    # delete the stack if not already in progress
    client = boto3.client('cloudformation')
    client.delete_stack(StackName=stack_name)

    # wait for stack to be gone
    return _wait_for_status(stack_name, '')


def build_image(image_name: str) -> bool:
    """
    Kick off the ImageBuilder pipeline
    :image_name: ImageBuilder pipeline name
    :return: True if started successfully, otherwise False
    """
    # get the pipeline ARN
    client = boto3.client('imagebuilder')
    response = client.list_image_pipelines(filters=[{'name': 'name', 'values': [image_name]}])

    # check for errors in the response
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        print('Failed to read image pipelines from AWS account.')
        return False

    # get the pipeline ARN
    pipeline_arn = None
    for pipeline in response['imagePipelineList']:
        if pipeline['name'] == image_name:
            pipeline_arn = pipeline['arn']

    # verify we found a pipeline
    if pipeline_arn is None:
        print('Failed to find image pipeline ARN from AWS account.')
        return False

    # start the image builder pipeline execution
    response = client.start_image_pipeline_execution(imagePipelineArn=pipeline_arn)
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        print('Failed to start pipeline execution.')
        return False

    # Successful if we made it this far
    print('Started image build.')
    return True


def check_status(stack_name: str) -> bool:
    """
    Check and print the status of a stack
    :stack_name: Name of the stack to check
    :return: True if successful, otherwise False
    """
    # get the stack status
    status = _get_stack_status(stack_name)

    # check for errors in the status check
    if not status:
        print(f'Failed to check status of {stack_name}')
        return False

    # print the status
    _print_status(stack_name, status)
    return True


def list_available_images() -> None:
    """
    Show a list of available AMIs for WRF from the ImageBuilder
    """
    # get a list of images
    images = _get_images()

    # print all images found
    for image in images:
        print('%s ... %s ... %s' % (image['ami'], image['dt'], image['name']))


def _get_images() -> List[dict]:
    """
    Get a list of available AMIs for WRF from the ImageBuilder
    :return: A list of dictionaries, which have attributes: name, ami, dt
    """
    # describe available images
    client = boto3.client('ec2')
    response = client.describe_images(Owners=['self'])

    # check response for errors
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        print('Error listing images.')
        return []

    # extract any images created by ImageBuilder with their AMIs
    images = []
    for image in response['Images']:
        if 'Tags' in image:
            for tag in image['Tags']:
                if tag['Key'] == 'Ec2ImageBuilderArn':
                    images.append(
                        {
                            'name': tag['Value'],
                            'ami': image['ImageId'],
                            'dt': image['CreationDate']
                        }
                    )

    # return the list of images
    return images


def _get_stack_status(stack_name: str) -> str:
    """
    Get the status of a CloudFormation stack
    :stack_name: Name of the stack
    :return: Stack status as a string (e.g. CREATE_COMPLETE)
    """
    try:
        # get a cloudformation client
        client = boto3.client('cloudformation')

        # describe the stack
        response = client.describe_stacks(StackName=stack_name)

        # check response for errors
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            return ''

        # return the stack status
        return response['Stacks'][0]['StackStatus']
    except Exception as e:
        print(e)
        return ''


def _wait_for_status(stack_name: str, target_status: str) -> bool:
    """
    Wait for the specified stack to reach the target status
    :stack_name: Name of the stack to watch
    :target_status: Return when we reach this status
    :return: True if target status reached, otherwise false
    """
    while True:
        # get the stack status
        status = _get_stack_status(stack_name)

        # print the status
        _print_status(stack_name, status)

        # check if we have reached the target status
        if status == target_status:
            return True

        # return if stack does not exist
        if status == '':
            return False

        # sleep for a bit
        time.sleep(2)


def _print_status(stack_name: str, status: str) -> None:
    """
    Print the status of the stack to stdout
    :stack_name: Name of the stack
    :status: Status of the stack
    """
    now = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S %z')
    print(f'{now} ... {stack_name} ... {status}')


def main():
    """
    Handle command line parameters
    """
    # setup the arg parser
    commands = ['create', 'delete', 'replace', 'build', 'status', 'list']
    parser = ArgParse(description='NCAR AWS - WRF ImageBuilder', formatter_class=HelpFormatter)
    parser.add_argument('command', help='Command to run', type=str, choices=commands)
    parser.add_argument('--stack-name', help='Name of the ImageBuilder stack', type=str, default='WrfImageBuilder')
    args = parser.parse_args()

    if args.command == 'create':
        create_stack(args.stack_name)
    elif args.command == 'delete':
        delete_stack(args.stack_name)
    elif args.command == 'replace':
        replace_stack(args.stack_name)
    elif args.command == 'status':
        check_status(args.stack_name)
    elif args.command == 'build':
        build_image(f'wrf-{args.stack_name}')
    elif args.command == 'list':
        list_available_images()
    else:
        print(f'Unknown command: {args.command}')
