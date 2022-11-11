import os
from wrfcloud.system import init_environment
from wrfcloud.api.handler import lambda_handler as real_lambda_handler


def lambda_handler(event: dict, context: any) -> dict:
    """
    Simple function to call the real lambda handler
    :param event: Event to the lambda
    :param context: Lambda context
    :return: Response
    """
    deployment_type = os.environ['DEPLOYMENT_TYPE']
    init_environment(deployment_type)
    return real_lambda_handler(event, context)
