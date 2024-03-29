"""
API actions that are responsible for reading WRF data
"""
import os
import base64
import gzip
import pkgutil
from typing import Union
from datetime import datetime, timedelta
from pytz import utc
from wrfcloud.api.auth import create_jwt
from wrfcloud.api.actions.action import Action
from wrfcloud.aws.pcluster import WrfCloudCluster, CustomAction
from wrfcloud.jobs import WrfJob, JobDao, LatLonPoint


class GetWrfMetaData(Action):
    """
    Get meta data for all the available WRF runs
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        required_fields = []
        return self.check_request_fields(required_fields, [])

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        try:
            # get a data access object
            dao = JobDao()

            # get all the jobs in the system
            jobs = dao.get_all_jobs()

            # add the list of jobs to the response
            self.response['jobs'] = [job.sanitized_data for job in jobs]
        except Exception as e:
            self.log.error('Failed to read model configurations.', e)
            self.errors.append('Failed to read model configurations.')
            return False

        return True


class GetWrfGeoJson(Action):
    """
    Get meta data for all the available WRF runs
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        required_fields = ['job_id', 'valid_time', 'variable']
        allowed_fields = ['z_level']
        return self.check_request_fields(required_fields, allowed_fields)

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        try:
            # get a geojson file
            job_id: str = self.request['job_id']
            valid_time: int = self.request['valid_time']
            variable: str = self.request['variable']
            z_level: int = self.request['z_level'] if 'z_level' in self.request else 0
            data = self._read_geojson_data(job_id, valid_time, variable, z_level)
            if data is None:
                return False
            self.response['geojson'] = base64.b64encode(data).decode()

            # put the request parameters back in the response
            self.response['job_id'] = job_id
            self.response['valid_time'] = valid_time
            self.response['variable'] = variable
            self.response['z_level'] = z_level
        except Exception as e:
            self.log.error('Failed to read model configurations.', e)
            self.errors.append('Failed to read model configurations.')
            return False

        return True

    def _read_geojson_data(self, job_id: str, valid_time: int, variable: str, z_level: int) -> Union[bytes, None]:
        """
        Read a geojson file from S3
        :param job_id: The model configuration name
        :param valid_time: The data valid time requested
        :param variable: The model variable requested
        :param z_level: Pressure level, or zero for 2D variable
        :return: GeoJSON data as stored in S3 (probably gzipped)
        """
        # get the job configuration
        dao = JobDao()
        job: WrfJob = dao.get_job_by_id(job_id)

        # make sure we found the right job ID
        if job is None:
            self.errors.append(f'Could not find job ID: {job_id}')
            self.log.error(f'Could not find job ID: {job_id}')
            return None

        # find the requested valid time
        s3_url: Union[str, None] = None
        for layer in job.layers:
            match_valid_time: bool = valid_time == layer.dt
            match_variable: bool = variable == layer.variable_name
            match_z_level: bool = (z_level == 0 and layer.z_level is None) or z_level == layer.z_level
            if match_valid_time and match_variable and match_z_level:
                s3_url = layer.layer_data
                break

        # make sure we found the requested valid time
        if s3_url is None:
            self.errors.append('Could not find requested data layer.')
            self.log.error(f'Could not find requested data layer: {job_id} {valid_time} {variable} {z_level}')
            return None

        # get the key from the S3 url
        bucket: str = s3_url.split('/')[2]
        key: str = '/'.join(s3_url.split('/')[3:])

        # read the object from S3
        data = self._s3_read(bucket, key)

        # unzip the data -- the whole response gets compressed again later
        return gzip.decompress(data)


class RunWrf(Action):
    """
    Run the WRF model
    """

    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        required_fields = ['job_name', 'configuration_name', 'start_time', 'forecast_length', 'output_frequency',
                           'notify']
        return self.check_request_fields(required_fields, [])

    def perform_action(self) -> bool:
        """
        Abstract method that performs the action and sets the response field
        :return: True if the action ran successfully
        """
        try:
            # create the run configuration file
            forecast_len_sec = self.request['forecast_length']
            start_date = utc.localize(datetime.utcfromtimestamp(self.request['start_time']))
            increment = timedelta(seconds=forecast_len_sec)
            end_time = start_date + increment

            # create a JWT to allow the cluster to delete itself when finished
            jwt = self._create_cluster_jwt()

            # create the custom action to start the model
            script_template = pkgutil.get_data('wrfcloud', 'api/actions/resources/run_wrf_template.sh').decode()
            script = script_template\
                .replace('__JOB_ID__', self.ref_id)\
                .replace('__S3_BUCKET__', os.environ['WRFCLOUD_BUCKET'])\
                .replace('__APP_HOSTNAME__', os.environ['APP_HOSTNAME'])\
                .replace('__API_HOSTNAME__', os.environ['API_HOSTNAME'])\
                .replace('__ADMIN_EMAIL__', os.environ['ADMIN_EMAIL'])\
                .replace('__JWT__', jwt)
            ca = CustomAction(self.ref_id, script)

            # create information for a new job
            job: WrfJob = WrfJob()
            job.job_id = self.ref_id
            job.job_name = self.request['job_name']
            job.configuration_name = self.request['configuration_name']
            job.start_dt = start_date
            job.end_dt = end_time
            job.forecast_length = forecast_len_sec
            job.output_frequency = self.request['output_frequency']
            job.input_frequency = 10800
            job.status_code = WrfJob.STATUS_CODE_STARTING
            job.status_message = 'Launching cluster'
            job.user_email = self.run_as_user.email
            job.notify = self.request['notify']
            job.domain_center = LatLonPoint({'latitude': 0, 'longitude': 0})

            # add the job information to the database
            job_dao = JobDao()
            job_added = job_dao.add_job(job)
            if not job_added:
                self.log.warn('Failed to add job information to database.')

            # start the cluster
            wrfcloud_cluster = WrfCloudCluster(self.ref_id)
            if self.client_ip is not None:
                wrfcloud_cluster.set_ssh_security_group_ip(self.client_ip + '/32')
            wrfcloud_cluster.print_summary()
            wrfcloud_cluster.create_cluster(ca, False)

        except Exception as e:
            self.log.error('Failed to launch WRF job', e)
            self.errors.append('Failed to launch WRF job')
            return False

        return True

    def _create_cluster_jwt(self) -> str:
        """
        Create a JWT to allow the cluster to delete itself when finished
        :return: JWT value
        """
        # construct a payload with a cluster role and email is the reference ID
        payload = {'email': self.ref_id, 'role': 'cluster'}

        # set the expiration date to be 96 hours from now
        expiration = 3600 * 96  # 96 hours

        # create and return the JWT
        return create_jwt(payload, expiration)


class DeleteCluster(Action):
    """
    Delete a cluster
    """

    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        required_fields = []
        optional_fields = []
        return self.check_request_fields(required_fields, optional_fields)

    def perform_action(self) -> bool:
        """
        Delete a cluster
        :return: True if the action ran successfully
        """
        try:
            # only a 'cluster' role will have permission to run this action, and it will
            # not be a real user the job_id will be set as the user's email address
            cluster_name: str = self.run_as_user.email
            cluster = WrfCloudCluster(cluster_name)
            cluster.delete_cluster()
        except Exception as e:
            self.log.error('Failed to delete cluster', e)
            self.errors.append('Failed to delete cluster')
            return False

        return True
