#!/usr/bin/env python3

"""
Functions for getting input GRIB data from remote sources.
"""

import datetime
import glob
import itertools
import math
import os
import requests
import yaml
from string import ascii_uppercase

from logging import Logger
from wrfcloud.runtime import RunInfo

def get_grib_input(runinfo: RunInfo, logger: Logger) -> None:
    """
    Gets GRIB files from external source for processing by ungrib

    The first attempt will be to grab data from NOMADS:
    https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod

    If there is a data outage or are running a retrospective case >10 days old, will attempt to pull from NOAA S3 bucket:
    https://registry.opendata.aws/noaa-gfs-bdp-pds/

    :param runinfo: Run information object
    :param logger: Logging object
    :return: None
    """
    logger.debug('Getting GRIB file(s) from external source (NOMADS or AWS S3)')

    # Get requested input data frequency (in sec) from namelist and convert to hours.
    input_freq_sec = runinfo.input_freq_sec
    input_freq_h = input_freq_sec / 3600.

    # Get requested initialization start time and set/format necessary start time info.
    cycle_start = runinfo.startdate
    cycle_start = datetime.datetime.strptime(cycle_start, '%Y-%m-%d_%H:%M:%S')
    cycle_start_ymd = cycle_start.strftime('%Y%m%d')
    cycle_start_h = cycle_start.strftime('%H')

    # Get requested end time of initialization and set/format necessary end time info.
    cycle_end = runinfo.enddate
    cycle_end = datetime.datetime.strptime(cycle_end, '%Y-%m-%d_%H:%M:%S')
    cycle_end_h = cycle_end.strftime('%H')

    # Calculate the forecast length in seconds and hours. Hours must be an integer.
    cycle_dt = cycle_end - cycle_start
    cycle_dt_s = cycle_dt.total_seconds()
    cycle_dt_h = math.ceil(cycle_dt_s / 3600.)

    # Set base URLs for NOMADS and S3 bucket with GFS data.
    #nomads_base_url = os.environ['NOMADS_BASE_URL']
    nomads_base_url = os.environ['NOAMDS_BASE_URL']
    aws_base_url = os.environ['AWS_BASE_URL']
    #nomads_base_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod'
    #aws_base_url = 'https://noaa-gfs-bdp-pds.s3.amazonaws.com'
    #aws_base_url = os.environ['AWS_BASE_URL'] 

    # Check if URL is valid (need to add logging).
    for fhr in range(0, cycle_dt_h + 1, int(input_freq_h)):
        gfs_file = f"gfs.{cycle_start_ymd}/{cycle_start_h}/atmos/gfs.t{cycle_start_h}z.pgrb2.0p25.f{fhr:03d}"
        gfs_local = f"gfs.t{cycle_start_h}z.pgrb2.0p25.f{fhr:03d}"

        try:
            full_url = os.path.join(nomads_base_url, gfs_file)
            nomads_ok = download_to_file(full_url, gfs_local)
            if nomads_ok:
                logger.debug(f'Pulled forecast hour {fhr} from NOMADS.')
            else:
                logger.debug(f'NOMADS URL does not exist for forecast hour {fhr}, trying AWS S3.')
                full_url = os.path.join(aws_base_url, gfs_file)
                aws_ok = download_to_file(full_url, gfs_local)
                if aws_ok:
                    logger.debug(f'Pulled forecast hour {fhr} from AWS S3.')
                if not nomads_ok and not aws_ok:
                    raise RuntimeError(f'GFS data not found for forecast hour {fhr}.')
        except:
            # Should this be a critical error that exits?
            logger.warning('NOMADS and AWS S3 URLs do not exist; this is bad!')

def download_to_file(url: str, local_file: str) -> bool:
    """
    Download a URL to a local file
    :param url: The URL to download
    :param local_file: Full- or relative-path to the local file (will be overwritten if exists!)
    :return: True if successful, otherwise False
    """
    try:
        # try to download and save the URL data
        response = requests.get(url)
        if response.status_code < 400:
            with open(local_file, 'wb') as gfs_file_out:
                gfs_file_out.write(response.content)
                gfs_file_out.close()
            return True
    except Exception:
        return False
