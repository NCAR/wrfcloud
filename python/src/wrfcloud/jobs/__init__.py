"""
Other code calling the wrfcloud.jobs module should mainly use functions from
this file.  Calling other functions and classes may have unexpected results.
"""
__all__ = ['WrfJob', 'JobDao', 'add_job_to_system', 'get_job_from_system', 'get_all_jobs_in_system',
           'update_job_in_system', 'delete_job_from_system']

from typing import Union, List
from wrfcloud.log import Logger
from wrfcloud.jobs.job import WrfJob
from wrfcloud.jobs.job_dao import JobDao


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


def get_all_jobs_in_system() -> List[WrfJob]:
    """
    Get a list of all jobs in the system
    :return: A list of all jobs in the system
    """
    # create the data access object
    dao = JobDao()

    return dao.get_all_jobs()


def update_job_in_system(update_job: WrfJob) -> bool:
    """
    Use the DAOs to update a job in the system
    :param update_job: The complete job object with updated values (only status fields are mutable)
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

    return False
