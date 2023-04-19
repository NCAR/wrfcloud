import wrfcloud.system
from wrfcloud.jobs import WrfJob
from wrfcloud.jobs import add_job_to_system
from wrfcloud.jobs import get_job_from_system
from wrfcloud.jobs import get_all_jobs_in_system
from wrfcloud.jobs import update_job_in_system
from wrfcloud.jobs import delete_job_from_system
from helper import _test_setup, _test_teardown, _get_sample_job, _get_all_sample_jobs

# initialize the test environment
wrfcloud.system.init_environment(env='test')


# TODO: This test needs S3 access in the test environment -- need to consider a different testing method
# def test_add_job() -> None:
#     """
#     Test the add job function
#     :return: None
#     """
#     # set up the test resources
#     assert _test_setup()
#
#     # create sample job
#     job = _get_sample_job(WrfJob.STATUS_CODE_PENDING)
#
#     # add the job to the database
#     assert add_job_to_system(job)
#
#     # retrieve the job from the database
#     job_ = get_job_from_system(job_id=job.job_id)
#
#     assert isinstance(job_.layers, list)
#
#     # compare the original and retrieved job data
#     for key in job.data:
#         assert key in job_.data
#         assert job.data[key] == job_.data[key]
#
#     # test getting a job with no job ID
#     empty_job_id = ''
#     if empty_job_id == '':
#         empty_job_id = None
#     assert get_job_from_system(empty_job_id) is None
#
#     # teardown the test resources
#     assert _test_teardown()


# TODO: This test needs S3 access in the test environment -- need to consider a different testing method
# def test_update_job() -> None:
#     """
#     Test the operations to update and read a job
#     :return: None
#     """
#     # set up the test resources
#     assert _test_setup()
#
#     # create sample job
#     job = _get_sample_job(WrfJob.STATUS_CODE_PENDING)
#
#     # add the job to the database
#     assert add_job_to_system(job)
#
#     # retrieve the job from the database
#     job_ = get_job_from_system(job_id=job.job_id)
#
#     # compare the original and retrieved job data
#     for key in job.data:
#         assert key in job_.data
#         assert job.data[key] == job_.data[key]
#
#     # update some job attributes
#     updated_job = _get_sample_job(WrfJob.STATUS_CODE_RUNNING)
#     job.update(updated_job.data)
#     assert update_job_in_system(job)
#
#     assert isinstance(job.layers, list)
#
#     # retrieve the job from the database
#     job_ = get_job_from_system(job_id=job.job_id)
#
#     # check the updated fields
#     assert job_.status_code == job.status_code
#     assert job_.status_message == job.status_message
#     assert job_.progress == job.progress
#
#     # update a job that does not exist in the database
#     job.job_id = 'UNKNOWNID'
#     assert not update_job_in_system(job)
#
#     # teardown the test resources
#     assert _test_teardown()


# TODO: This test needs S3 access in the test environment -- need to consider a different testing method
# def test_delete_job() -> None:
#     """
#     Test deleting a job
#     :return: None
#     """
#     # set up the test resources
#     assert _test_setup()
#
#     # create sample job
#     job = _get_sample_job(WrfJob.STATUS_CODE_RUNNING)
#
#     # add the job to the database
#     assert add_job_to_system(job)
#
#     # retrieve the job from the database
#     job_ = get_job_from_system(job_id=job.job_id)
#     assert job_ is not None
#
#     # delete the job from the database
#     assert delete_job_from_system(job)
#
#     # make sure the job is gone
#     job_ = get_job_from_system(job_id=job.job_id)
#     assert job_ is None
#
#     # try to delete a with invalid data
#     assert not delete_job_from_system(None)
#
#     # teardown the test resources
#     assert _test_teardown()


# TODO: This test needs S3 access in the test environment -- need to consider a different testing method
# def test_get_all_jobs() -> None:
#     """
#     Test the get all jobs function
#     :return: None
#     """
#     # set up the test resources
#     assert _test_setup()
#
#     # get all sample jobs
#     jobs = _get_all_sample_jobs()
#
#     # add all the jobs to the system
#     for job in jobs:
#         assert add_job_to_system(job)
#
#     # get all the jobs in the system
#     jobs_ = get_all_jobs_in_system()
#
#     # compare the jobs retrieved to the jobs expected
#     assert len(jobs) == len(jobs_)
#     for job in jobs:
#         for job_ in jobs_:
#             if job.job_id == job_.job_id:
#                 assert job.data == job_.data
#
#     # teardown the test resources
#     assert _test_teardown()
