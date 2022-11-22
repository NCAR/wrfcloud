"""
The SubscriberDao class is a data access object that performs basic CRUD
(create, read, update, delete) functions on the subscriber database.
"""

import os
import json
from typing import List, Union
from wrfcloud.system import get_aws_session
from wrfcloud.schedule.schedule import Schedule
from wrfcloud.log import Logger


class ScheduleDao:
    """
    CRUD operations for scheduled jobs
    """

    def __init__(self):
        """
        Create the Data Access Object (DAO)
        """
        self.log = Logger(self.__class__.__name__)
        self.aws_client = None  # type is botocore.client.EventBridge, but this will not import correctly

    def add_schedule(self, schedule: Schedule) -> bool:
        """
        Store a new schedule
        :param schedule: Schedule object to store
        :return: True if successful, otherwise False
        """
        # get an AWS session and events client
        client = self._get_client()

        # create the rule name
        rule_prefix = os.environ['EVENTBRIDGE_RULE_PREFIX']
        rule_name = f'{rule_prefix}-{schedule.ref_id}'

        # put a rule with cron expression into the system
        hours = ','.join([str(hour) for hour in schedule.daily_hours])
        put_rule_res = client.put_rule(
            Name=rule_name,
            ScheduleExpression=f'cron(0 {hours} * * ? *)',
            State='ENABLED',
            Description=schedule.api_request['data']['configuration_name']
        )

        # check the response for errors
        if put_rule_res['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise RuntimeError('Failed to add schedule to EventBridge (rule).')

        # create the event for the lambda function
        event = {
            'source': 'aws.events',
            'schedule': schedule.data,
            'request': schedule.api_request
        }

        # add a target to the new rule --
        put_targets_res = client.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    'Id': f'{rule_name}-lambda-invoke',
                    'Arn': schedule.function_arn,
                    'Input': json.dumps(event),
                    'RetryPolicy': {
                        'MaximumEventAgeInSeconds': 300,
                        'MaximumRetryAttempts': 5
                    }
                }
            ]
        )

        # check the response for errors
        if put_targets_res['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise RuntimeError('Failed to add schedule to EventBridge (target).')

        return True

    def get_all_schedules(self) -> List[Schedule]:
        """
        Get a list of all schedule in the system
        :return: List of all schedules
        """
        # get a list of rules
        rules = self._get_all_rules()

        # get the target for each rule and add to a schedule
        schedules: List[Schedule] = []
        for rule in rules:
            # get the target for the rule
            target = self._get_target(rule['Name'])

            # retrieve the schedule data from the target input
            event = json.loads(target['Input'])
            schedule = Schedule(event['schedule'])
            schedules.append(schedule)

        return schedules

    def delete_schedule(self, schedule: Schedule) -> bool:
        """
        Delete the schedule from the event bus
        :param schedule: Subscriber object
        :return: True if successful, otherwise False
        """
        # create the rule name
        rule_prefix = os.environ['EVENTBRIDGE_RULE_PREFIX']
        rule_name = f'{rule_prefix}-{schedule.ref_id}'

        # get an AWS client
        client = self._get_client()

        # delete the target
        target = self._get_target(rule_name)
        if target:
            res = client.remove_targets(Rule=rule_name, Ids=[target['Id']])
            if res['ResponseMetadata']['HTTPStatusCode'] != 200:
                self.log.error(f'Failed to delete rule\'s target: {rule_name}')
                return False

        # delete the rule
        res = client.delete_rule(Name=rule_name)
        if res['ResponseMetadata']['HTTPStatusCode'] != 200:
            self.log.error(f'Failed to delete rule: {schedule.ref_id}')
            return False

        return True

    def _get_client(self):
        """
        Get a client object for the AWS Events service
        """
        if self.aws_client is None:
            session = get_aws_session()
            self.aws_client = session.client('events')
        return self.aws_client

    def _get_all_rules(self) -> List[dict]:
        """
        Get a list of all the rules in the account's default event bus
        """
        # get an AWS session and events client
        client = self._get_client()

        # retrieve a list of rules
        rules: List[dict] = []
        next_token = None
        first = True
        while first or next_token is not None:
            # mark the first time in this loop
            first = False

            # query the event bus for its rules
            res = client.list_rules() if next_token is None else \
                  client.list_rules(NextToken=next_token)

            # check the response for errors
            if res['ResponseMetadata']['HTTPStatusCode'] != 200:
                raise RuntimeError('AWS EventBridge request failed.')

            # store the rules
            for rule in res['Rules']:
                rules.append(rule)

            # check for a "next token"
            if 'NextToken' in res:
                next_token = res['NextToken']

        return rules

    def _get_target(self, rule_name: str) -> Union[None, dict]:
        """
        Get the target for the specified rule
        :param rule_name: Get target for this rule name
        :return: The rule's target
        """
        # get an AWS session and events client
        client = self._get_client()

        # get the target
        res = client.list_targets_by_rule(Rule=rule_name)
        if res['ResponseMetadata']['HTTPStatusCode'] != 200:
            self.log.warn(f'Failed to get targets for rule: {rule_name}')

        # we always have only one target per rule
        target = res['Targets'][0]

        return target
