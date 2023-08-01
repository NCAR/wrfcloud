"""
Test the wrfcloud.schedule module
"""


from wrfcloud.system import init_environment
from wrfcloud.schedule import Schedule, ScheduleDao
from wrfcloud.api.handler import create_reference_id
from wrfcloud.api.auth import create_jwt

# Initialize the test environment
init_environment('test')


# TODO: This test needs access to AWS account resources and does not run in the test environment.
# def test_scheduled_job_dao():
#     """
#     Test the function to get all scheduled jobs
#     """
#     # create a new schedule object
#     ref_id = create_reference_id()
#     email = 'user@domain.tld'
#     schedule = Schedule(
#         {
#             'ref_id': ref_id,
#             'function_arn': 'arn:aws:lambda:us-east-2:119569266530:function:development_wrfcloud_handler',
#             'daily_hours': [0, 6, 18],
#             'email': email,
#             'api_request': {
#                 'action': 'RunWrf',
#                 'jwt': create_jwt({'email': email}),
#                 'data': {
#                     'configuration_name': 'test',
#                     'start_time': 0,
#                     'forecast_length': 86400,
#                     'output_frequency': 3600,
#                     'notify': True
#                 }
#             }
#         }
#     )
#
#     dao = ScheduleDao()
#     assert dao.add_schedule(schedule)
#
#     # get the scheduled jobs
#     schedules = dao.get_all_schedules()
#     assert len(schedules) == 1
#
#     # delete the schedule job
#     assert dao.delete_schedule(schedule)
#
#     # make sure there are no schedule jobs left
#     schedules = dao.get_all_schedules()
#     assert len(schedules) == 0
