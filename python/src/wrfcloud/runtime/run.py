"""
Wrapper script for creating, submitting, and monitoring runs of the wrfcloud framework.

This script takes a single argument: --name='name' should be set to a unique alphanumeric name
for this particular run of the system. If no name is given, a test configuration will be
run.
"""

import argparse
import os
from typing import Union
from wrfcloud.runtime.geogrid import GeoGrid
from wrfcloud.runtime.ungrib import Ungrib
from wrfcloud.runtime.metgrid import MetGrid
from wrfcloud.runtime.real import Real
from wrfcloud.runtime.wrf import Wrf
from wrfcloud.runtime.postproc import UPP, GeoJson
from wrfcloud.config import WrfConfig, get_config_from_system
from wrfcloud.jobs import WrfJob, get_job_from_system, update_job_in_system
from wrfcloud.aws.pcluster import WrfCloudCluster
from wrfcloud.system import init_environment, get_aws_session
from wrfcloud.log import Logger


def main() -> None:
    """
    Main routine that creates a new run and monitors it through completion
    """
    init_environment('cli')
    log = Logger()
    job: Union[WrfJob, None] = None
    try:
        log.debug('Reading command line arguments')
        parser = argparse.ArgumentParser()
        parser.add_argument('--job-id', type=str, help='Job ID with run details.', required=True)
        args = parser.parse_args()
        job_id = args.job_id

        # get a job from the database
        job = get_job_from_system(job_id)

        # create the RunInfo object from the configuration file
        log.info(f'Starting new run "{job.job_id}"')
        log.debug('Creating new RunInfo')
        log.info(f'Setting up working directory {job.work_dir}')
        os.makedirs(job.work_dir, exist_ok=True)

        # set up the configuration
        config: WrfConfig = _load_model_configuration(job)
        job.cores = config.cores

        # maybe update the logger's application name to the reference ID
        log.APPLICATION_NAME = job.job_id or 'wrfcloud-run'
        log.application_name = job.job_id or 'wrfcloud-run'

        log.debug('Starting geogrid task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Running GEOGRID', 0)
        geogrid = GeoGrid(job)
        geogrid.start()
        log.debug(geogrid.get_run_summary())

        log.debug('Starting ungrib task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Running UNGRIB', 0.05)
        ungrib = Ungrib(job)
        ungrib.start()
        log.debug(ungrib.get_run_summary())

        log.debug('Starting metgrid task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Running METGRID', 0.1)
        metgrid = MetGrid(job)
        metgrid.start()
        log.debug(metgrid.get_run_summary())

        log.debug('Starting real task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Running REAL', 0.2)
        real = Real(job)
        real.start()
        log.debug(real.get_run_summary())

        log.debug('Starting wrf task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Running WRF', 0.3)
        wrf = Wrf(job)
        wrf.start()
        log.debug(wrf.get_run_summary())

        log.debug('Starting UPP task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Running UPP', 0.6)
        upp = UPP(job)
        upp.start()
        log.debug(upp.get_run_summary())

        log.debug('Starting GeoJSON task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Running GeoJSON converter', 0.8)
        geojson = GeoJson(job)
        geojson.set_grib_files(upp.grib_files)
        geojson.start()
        log.debug(geojson.get_run_summary())

        # send a notification if requested
        if job.notify:
            job.send_complete_notification()

        # final job and status update
        _update_job_status(job, WrfJob.STATUS_CODE_FINISHED, 'Done', 1)
    except Exception as e:
        log.error('Failed to run the model', e)
        if job:
            _update_job_status(job, WrfJob.STATUS_CODE_FAILED, 'Failed', 1)

    # Shutdown the cluster after completion or failure
    try:
        cluster = WrfCloudCluster(job.job_id)
        cluster.delete_cluster()
    except Exception as e:
        log.error('Failed to delete cluster.', e)
        _update_job_status(job, WrfJob.STATUS_CODE_FAILED,
                           'Failed to delete cluster, shutdown from AWS web console to avoid additional costs.', 1)


def _update_job_status(job: Union[None, WrfJob], status_code: int, status_message: str, progress: float) -> None:
    """
    Update the job status in the database and web applications
    :param job: Job object to update
    :param status_code: Status code see WrfJob.STATUS_CODE_*
    :param status_message: Message to set and pass to the user
    :param progress: Fraction complete 0-1
    """
    if not job:
        return

    Logger().info(f'Updating job status {job.job_id} {status_message}')
    job.status_code = status_code
    job.progress = progress
    job.status_message = status_message
    update_job_in_system(job, True)


def _load_model_configuration(job: WrfJob) -> WrfConfig:
    """
    Pull the namelists and geo_em file from S3 for the given config
    :param job: Details for the job
    :return: WRF model configuration object
    """
    # load the configuration data
    config: WrfConfig = get_config_from_system(job.configuration_name)

    # write out the namelist files
    os.makedirs(job.static_dir, exist_ok=True)
    with open(f'{job.static_dir}/namelist.input', 'w') as wrf_namelist:
        wrf_namelist.write(config.wrf_namelist)
        wrf_namelist.close()
    with open(f'{job.static_dir}/namelist.wps', 'w') as wps_namelist:
        wps_namelist.write(config.wps_namelist)
        wrf_namelist.close()
    try:
        s3 = get_aws_session().client('s3')
        bucket = os.environ['WRFCLOUD_BUCKET']
        key = config.s3_key_geo_em
        file = f'{job.static_dir}/geo_em.d01.nc'
        s3.download_file(bucket, key, file)
    except Exception as e:
        Logger().info('geo_em file not found -- must run geogrid process')

    return config
