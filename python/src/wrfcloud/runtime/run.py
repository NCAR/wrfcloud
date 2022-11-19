"""
Wrapper script for creating, submitting, and monitoring runs of the wrfcloud framework.

This script takes a single argument: --name='name' should be set to a unique alphanumeric name
for this particular run of the system. If no name is given, a test configuration will be
run.
"""

import argparse
import os
from typing import Union
from wrfcloud.runtime.ungrib import Ungrib
from wrfcloud.runtime.metgrid import MetGrid
from wrfcloud.runtime.real import Real
from wrfcloud.runtime.wrf import Wrf
from wrfcloud.runtime.postproc import UPP, GeoJson
from wrfcloud.runtime import RunInfo
from wrfcloud.jobs import WrfJob, get_job_from_system, update_job_in_system
from wrfcloud.aws.pcluster import WrfCloudCluster
from wrfcloud.system import init_environment
from wrfcloud.log import Logger


def main() -> None:
    """
    Main routine that creates a new run and monitors it through completion
    """
    init_environment('cli')
    log = Logger()
    job: Union[None, WrfJob] = None
    try:
        log.debug('Reading command line arguments')
        parser = argparse.ArgumentParser()
        parser.add_argument('--name', type=str, default='test',
                            help='"name" should be a unique alphanumeric name for this particular run')
        args = parser.parse_args()
        name = args.name

        # create the RunInfo object from the configuration file
        log.info(f'Starting new run "{name}"')
        log.debug('Creating new RunInfo')
        runinfo = RunInfo(name)
        log.info(f'Setting up working directory {runinfo.wd}')
        os.makedirs(runinfo.wd, exist_ok=True)

        # maybe update the logger's application name to the reference ID
        log.APPLICATION_NAME = runinfo.ref_id or 'wrfcloud-run'
        log.application_name = runinfo.ref_id or 'wrfcloud-run'

        # get a job from the database
        job = get_job_from_system(runinfo.ref_id) if runinfo.ref_id is not None else None

        log.debug('Starting ungrib task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Starting ungrib task', 0)
        ungrib = Ungrib(runinfo)
        ungrib.start()
        log.debug(ungrib.get_run_summary())

        log.debug('Starting metgrid task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Starting metgrid task', 0.1)
        metgrid = MetGrid(runinfo)
        metgrid.start()
        log.debug(metgrid.get_run_summary())

        log.debug('Starting real task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Starting real task', 0.2)
        real = Real(runinfo)
        real.start()
        log.debug(real.get_run_summary())

        log.debug('Starting wrf task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Starting wrf task', 0.3)
        wrf = Wrf(runinfo)
        wrf.start()
        log.debug(wrf.get_run_summary())

        log.debug('Starting UPP task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Starting UPP task', 0.6)
        upp = UPP(runinfo)
        upp.start()
        log.debug(upp.get_run_summary())

        log.debug('Starting GeoJSON task')
        _update_job_status(job, WrfJob.STATUS_CODE_RUNNING, 'Starting GeoJSON task', 0.8)
        geojson = GeoJson(runinfo)
        geojson.set_grib_files(upp.grib_files)
        geojson.start()
        log.debug(geojson.get_run_summary())

        _update_job_status(job, WrfJob.STATUS_CODE_FINISHED, 'Done', 1)
    except Exception as e:
        log.error('Failed to run the model', e)
        _update_job_status(job, WrfJob.STATUS_CODE_FAILED, 'Failed', 1)

    # Shutdown the cluster after completion or failure
    try:
        cluster = WrfCloudCluster(job.job_id)
        cluster.delete_cluster()
    except Exception as e:
        log.error('Failed to delete cluster.', e)
        _update_job_status(job, WrfJob.STATUS_CODE_FAILED, 'Failed to delete cluster, shutdown from AWS web console to avoid additional costs.', 1)


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

    print(f'Updating job status {job.job_id} {status_message}')  # TODO: Remove this, use a logger
    job.status_code = status_code
    job.progress = progress
    job.status_message = status_message
    update_job_in_system(job, True)
