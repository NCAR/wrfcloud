from typing import List
from wrfcloud.api.audit import AuditDao
from wrfcloud.api.auth.refresh import RefreshTokenDao
from wrfcloud.jobs import JobDao, WrfJob
from wrfcloud.config import WrfConfig
from wrfcloud.user import UserDao, User
from wrfcloud.subscribers import SubscriberDao, Subscriber
import yaml


def _test_setup() -> bool:
    """
    Setup required test resources (i.e. DynamoDB table in local dynamodb)
    :return: True if successful, otherwise False
    """
    try:
        # get a data access object
        user_dao = UserDao()
        audit_dao = AuditDao()
        refresh_dao = RefreshTokenDao()
        job_dao = JobDao()
        subscriber_dao = SubscriberDao()

        try:
            # just in case the table already exists, get rid of it
            user_dao.delete_table(user_dao.table)
            audit_dao.delete_table(audit_dao.table)
            refresh_dao.delete_table(refresh_dao.table)
            job_dao.delete_table(job_dao.table)
            subscriber_dao.delete_table(subscriber_dao.table)
        except Exception:
            pass

        # create the table
        return user_dao.create_user_table() and \
            audit_dao.create_audit_table() and \
            refresh_dao.create_refresh_table() and \
            job_dao.create_job_table() and \
            subscriber_dao.create_subscriber_table()
    except Exception as e:
        print(e)
        return False


def _test_teardown() -> bool:
    """
    Delete resources created by the tests
    :return: True if successful, otherwise False
    """
    try:
        # delete the table
        user_dao = UserDao()
        audit_dao = AuditDao()
        refresh_dao = RefreshTokenDao()
        job_dao = JobDao()
        subscriber_dao = SubscriberDao()

        user_dao.delete_table(user_dao.table)
        audit_dao.delete_table(audit_dao.table)
        refresh_dao.delete_table(refresh_dao.table)
        job_dao.delete_table(job_dao.table)
        subscriber_dao.delete_table(subscriber_dao.table)
    except Exception as e:
        print(e)
        return False

    return True


def _get_sample_user(role_id: str) -> (User, str):
    """
    Get a sample user with an admin role
    :return: A sample user and its plain text password
    """
    # load sample users
    sample_users = yaml.safe_load(open('resources/sample_users.yaml'))

    # get the first admin entry
    admin_data = sample_users['users'][role_id][0]
    admin = User(admin_data)

    # make sure the password was hashed
    assert admin.password != admin_data['password']

    # return the sample admin user
    return admin, admin_data['password']


def _get_all_sample_users() -> List[User]:
    """
    Get a sample user with an admin role
    :return: A sample user and its plain text password
    """
    # load sample users
    sample_users = yaml.safe_load(open('resources/sample_users.yaml'))

    # get the first admin entry
    users = []
    for role in sample_users['users']:
        for user_data in sample_users['users'][role]:
            user = User(user_data)
            assert user.password != user_data['password']
            users.append(user)

    # return the sample users
    return users


def _get_sample_job(status_code: int) -> WrfJob:
    """
    Get a sample job with a given status
    :return: A sample job object
    """
    # load sample jobs
    sample_jobs = yaml.safe_load(open('resources/sample_jobs.yaml'))['jobs']
    job_data = sample_jobs[status_code][0]
    return WrfJob(job_data)


def _get_all_sample_jobs() -> List[WrfJob]:
    """
    Get a list of all sample jobs
    :return: List of sample jobs
    """
    # load sample jobs
    sample_jobs = yaml.safe_load(open('resources/sample_jobs.yaml'))['jobs']
    jobs_data = []

    # get jobs of all status codes if status code is not provided...
    for job_data in [job for job_group in sample_jobs for job in job_group]:
        jobs_data.append(job_data)

    # build job objects and return them
    return [WrfJob(job_data) for job_data in jobs_data]


def _get_all_sample_wrf_configurations() -> List[WrfConfig]:
    """
    Get a list of all sample WRF configs
    :return: List of sample WRF configs
    """
    # load sample configs
    sample_configs = [yaml.safe_load(open('resources/sample_wrf_configs.yaml'))]

    return [WrfConfig(config_data) for config_data in sample_configs]


def _get_sample_subscriber() -> Subscriber:
    """
    Get a sample subscriber
    :return: A sample subscriber object
    """
    # load sample subscribers
    sample_subscribers = yaml.safe_load(open('resources/sample_subscribers.yaml'))['subscribers']

    # return the first one in the list
    return Subscriber(sample_subscribers[0])


def _get_all_sample_subscribers() -> List[Subscriber]:
    """
    Get all the sample subscribers
    :return: A list of sample subscriber objects
    """
    # load sample subscribers
    sample_subscribers = yaml.safe_load(open('resources/sample_subscribers.yaml'))['subscribers']

    # create and return a list of all sample subscribers
    return [Subscriber(data) for data in sample_subscribers]
