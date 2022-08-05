#!/usr/bin/env python3

"""
Functions for setting up, executing, and monitoring a run of the WPS program ungrib
"""

import boto3
import datetime
import glob
import itertools
import math
import os
#import urllib3
import urllib.error
import urllib.request
import requests
from string import ascii_uppercase
from logging import Logger
from f90nml.namelist import Namelist

# Import our custom modules
from wrfcloud.runtime.tools.make_wps_namelist import make_wps_namelist
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
    logger.debug(f'test')

    if runinfo.local_data:
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
    else:
        logger.debug('Getting GRIB file(s) from external source (NOMADS or S3 bucket)')

        # NOMADS provides data in realtime with a retention preiod of ~10 days. We will
        # first look at NOMADS for data. If data does not exist, or initialization 
        # requested is greater than the retention period, we will pull data from S3 bucket.
        # Data on the S3 bucket is avaialble after the full model run is complete (i.e.,
        # not quite real time), but the archive is for several years.
        nomads_retention = 10. # in days

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
        aws_base_url = 'https://noaa-gfs-bdp-pds.s3.amazonaws.com/index.html#'

        # Check to see if the requested initialization time is greater than NOMADS retention.
        request_dt = datetime.datetime.now() - cycle_start
        request_dt_s = request_dt.total_seconds()
        if request_dt_s <= nomads_retention*86400:
            get_method = 'NOMADS'
        else:
            get_method = 'S3'

        # Beef this up to include cycle date and forecast length.        
        logger.debug(f'Attempting to get from from {get_method}.')

        # Set base URLs for NOMADS and S3 bucket with GFS data.
        nomads_base_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod'
        aws_base_url = 'https://noaa-gfs-bdp-pds.s3.amazonaws.com/index.html#'

        #bucket_name = 'noaa-gfs-bdp-pds' # replace with your bucket name
        #s3 = boto3.resource('s3')

        #try:
        #    s3.Bucket(buket_name).download_file(KEY, 'my_local_image.jpg')
        #except botocore.exceptions.ClientError as e:
        #    if e.response['Error']['Code'] == "404":
        #    print("The object does not exist.")
        #else:
        #    raise

        # check if URL is valid (and add logging)
        if get_method == 'NOMADS':
            try:
                url_dir = nomads_base_url
                ret = urllib.request.urlopen(url_dir)
            except urllib.error.URLError as e:
                logger.warning('URL does not exist!') 


        #try:
        #    # Get the remote size
        #    ret = urllib.request.urlopen(remote_path)
        #    file_size_at_server = int(ret.info().get('content-length', '0'))
        #    ret.close()
        #except:
        #    logging.debug('File size retrieval failed.')
           
        

        for fhr in range (cycle_start.hour, cycle_dt_h, int(input_freq_h)):
            gfs_file = f"gfs.{cycle_start_ymd}/{cycle_start_h}/atmos/gfs.t{cycle_start_h}z.pgrb2.0p25.f{fhr:03d}"
            gfs_local = f"gfs.t{cycle_start_h}z.pgrb2.0p25.f{fhr:03d}"
            full_url = os.path.join(nomads_base_url, gfs_file)
            #print(full_url)
            #data = requests.get(full_url)
            urllib.request.urlretrieve(full_url, gfs_local)

            #s3.Bucket(BUCKET_NAME).download_file(gfs_file, gfs_local)
            
        
        #logger.warning('Not yet implemented!')


def get_files(runinfo: RunInfo, logger: Logger, namelist: Namelist) -> None:
    """Gets all input files necessary for running ungrib"""

    logger.debug('Getting GRIB input files')
    get_grib_input(runinfo, logger)

    logger.debug('Getting geo_em file(s)')
    # Get the number of domains from namelist
    for domain in range(1, namelist['share']['max_dom'] + 1):
        os.symlink(f'{runinfo.staticdir}/geo_em.d{domain:02d}.nc', f'geo_em.d{domain:02d}.nc')

    logger.debug('Getting VTable')


def main(runinfo: RunInfo, logger: Logger) -> None:
    """Main routine that sets up, runs, and monitors ungrib end-to-end"""
    logger.info(f'Setting up ungrib for "{runinfo.name}"')

    # Stop execution if experiment working directory already exists
    if os.path.isdir(runinfo.ungribdir):
        errmsg = (f"Ungrib directory \n                 {runinfo.ungribdir}\n                 "
                  "already exists. Move or remove this directory before continuing.")
        logger.critical(errmsg)
        raise FileExistsError(errmsg)

    os.mkdir(runinfo.ungribdir)
    os.chdir(runinfo.ungribdir)
    logger.debug('Creating WPS namelist')
    namelist = make_wps_namelist(runinfo, logger)

    logger.debug('Getting ungrib input files')
    get_files(runinfo, logger, namelist)

    logger.warning(f"{__name__} isn't fully implemented yet!")


if __name__ == "__main__":
    print('Script not yet set up for standalone run, exiting...')
