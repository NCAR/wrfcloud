#!/usr/bin/env python3

"""
Functions for setting up and creating namelist.wps
"""

import datetime
import glob
import itertools
import math
import os
import requests
from string import ascii_uppercase

from logging import Logger
from wrfcloud.runtime import RunInfo

def get_grib_input(runinfo: RunInfo, logger: Logger) -> None:
    """
    Gets GRIB files for processing by ungrib

    If user has specified local data (or this is the test case), will attempt to read from that
    local data.

    Otherwise, will attempt to first grab data from NOMADS
    https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod

    If there is a data outage or are running a retrospective case >10 days old, will attempt to pull from NOAA S3 bucket
    https://registry.opendata.aws/noaa-gfs-bdp-pds/
    """
    if runinfo.local_data:
        get_grib_files_from_local_source(runinfo, logger)
    else:
        get_grib_files_from_remote_source(runinfo, logger)


def get_grib_files_from_local_source(runinfo: RunInfo, logger: Logger) -> None:
    """
    Get GRIB files from a local source
    :param runinfo: Run information object
    :param logger: Logging object
    :return: None
    """
    logger.debug('Getting GRIB file(s) from local source')
    # Iterator for generating letter strings for GRIBFILE suffixes. Don't blame me, this is ungrib's fault
    suffixes = itertools.product(ascii_uppercase, repeat=3)
    filelist = []
    # If runinfo.local_data is a string, convert it to a list
    if isinstance(runinfo.local_data, str):
        data = [runinfo.local_data]
    else:
        data = runinfo.local_data

    for entry in data:
        # Since there may be multiple string entries in runinfo.local_data, we need to parse
        # each one individually using glob.glob, then append them all together
        filelist.extend(sorted(glob.glob(entry)))
    for gribfile in filelist:
        # Gives us GRIBFILE.AAA on first iteration, then GRIBFILE.AAB, GRIBFILE.AAC, etc.
        griblink = 'GRIBFILE.' + "".join(suffixes.__next__())
        logger.debug(f'Linking input GRIB file {gribfile} to {griblink}')
        os.symlink(gribfile, griblink)

def get_grib_files_from_remote_source(runinfo: RunInfo, logger: Logger) -> None:
    """
    Get GRIB files from a remote source (NOMADS or AWS S3)
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
    nomads_base_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod'
    aws_base_url = 'https://noaa-gfs-bdp-pds.s3.amazonaws.com'

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
                    raise RuntimeError(f'GFS data not found for forecast hour {fhr}')
        except:
            logger.warning('NOMADS and AWS S3 URLs do not exist; this is bad!')

    # Iterator for generating letter strings for GRIBFILE suffixes. Don't blame me, this is ungrib's fault
    # Note: For pulling data from NOMADS or S3, we assume files start with gfs*
    suffixes = itertools.product(ascii_uppercase, repeat=3)
    filelist = glob.glob(os.path.join(runinfo.ungribdir, 'gfs.*'))

    for gribfile in filelist:
        # Gives us GRIBFILE.AAA on first iteration, then GRIBFILE.AAB, GRIBFILE.AAC, etc.
        griblink = 'GRIBFILE.' + "".join(suffixes.__next__())
        logger.debug(f'Linking input GRIB file {gribfile} to {griblink}')
        os.symlink(gribfile, griblink)

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
