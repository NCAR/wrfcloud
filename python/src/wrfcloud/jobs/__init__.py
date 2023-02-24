"""
Other code calling the wrfcloud.jobs module should mainly use functions from
this file.  Calling other functions and classes may have unexpected results.
"""
__all__ = ['WrfJob', 'JobDao', 'add_job_to_system', 'get_job_from_system', 'get_all_jobs_in_system',
           'update_job_in_system', 'delete_job_from_system', 'LatLonPoint', 'WrfLayer']

import os
from typing import Union, List
from wrfcloud.log import Logger
from wrfcloud.jobs.job import WrfJob
from wrfcloud.jobs.job_dao import JobDao
from wrfcloud.subscribers import message_all_subscribers
from wrfcloud.jobs.job import LatLonPoint
from wrfcloud.jobs.job import WrfLayer


log = Logger()


def add_job_to_system(new_job: WrfJob) -> bool:
    """
    Add a job to the system
    :param new_job: The new job to add
    :return True if added successfully
    """
    # get the DAOs
    dao = JobDao()

    # add the job and return status
    return dao.add_job(new_job)


def get_job_from_system(job_id: str) -> Union[WrfJob, None]:
    """
    Get a job from the system
    :param job_id: User job ID
    :return User with matching job ID, or None
    """
    # verify parameters
    if job_id is None:
        return None

    # get the job DAO
    dao = JobDao()

    # get job by job ID
    return dao.get_job_by_id(job_id)


def get_all_jobs_in_system(full_load: bool = True) -> List[WrfJob]:
    """
    Get a list of all jobs in the system
    :param full_load: Fully load the job data, or just the metadata (i.e. not including the layer information)
    :return: A list of all jobs in the system
    """
    # create the data access object
    dao = JobDao()

    return dao.get_all_jobs(full_load)


def update_job_in_system(update_job: WrfJob, notify_web: Union[bool, None] = None) -> bool:
    """
    Use the DAOs to update a job in the system
    :param update_job: The complete job object with updated values (only status fields are mutable)
    :param notify_web: Flag telling us to notify the web clients or not
    :return: True if successful, otherwise False
    """
    # create objects
    dao = JobDao()

    # get the existing job
    existing_job = dao.get_job_by_id(update_job.job_id)
    if existing_job is None:
        log.error('The job does not exist and cannot be updated: ' + update_job.job_id)
        return False

    # update job table
    update_job.job_id = existing_job.job_id  # job_id is immutable
    updated = dao.update_job(update_job)

    # message any websocket clients
    notify_web = os.environ['NOTIFY_WEB_CLIENTS'] if notify_web is None else notify_web
    if notify_web:
        update_message = _create_job_update_message(update_job)
        message_all_subscribers(update_message)

    return updated


def delete_job_from_system(del_job: WrfJob) -> bool:
    """
    Delete a job from the system
    :param del_job: Job to delete from the system
    :return True if deleted, otherwise False
    """
    # get the job DAO
    dao = JobDao()

    # delete job
    if del_job is not None:
        return dao.delete_job(del_job)

    log.error('Value for job to remove was set as None', ValueError('del_job cannot be None'))
    return False


def _create_job_update_message(update_job: WrfJob) -> dict:
    """
    Create a message describing this update that can be consumed by websocket clients
    :param update_job: The updated WRF job
    :return: A websocket message
    """
    message = {
        'type': 'JobStatus',
        'data': {
            'data': {
                'job': update_job.sanitized_data
            }
        }
    }
    return message
