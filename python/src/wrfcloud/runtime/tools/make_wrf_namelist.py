"""
Functions for setting up and creating namelist.input file
"""

import f90nml
from f90nml.namelist import Namelist
from wrfcloud.jobs import WrfJob
from wrfcloud.log import Logger


def make_wrf_namelist(job: WrfJob, nml_file: str = None) -> Namelist:
    """
    Main routine that sets up and creates namelist.input file
    :param job: Details of this job
    :param nml_file: Namelist file
    :return: Namelist object
    """
    log = Logger()
    log.debug(f'Setting up WRF namelist for "{job.job_id}"')

    if nml_file is None:
        nml_file = job.static_dir + '/namelist.input'

    with open(nml_file, encoding='utf-8') as namelist_file_read:
        namelist = f90nml.read(namelist_file_read)

    # Convert singlet values to lists of values (makes iterating easier)
    for namelist_line in namelist:
        for entry in namelist[namelist_line]:
            if isinstance(namelist[namelist_line][entry], (str, int, float, complex)):
                tempval = namelist[namelist_line][entry]
                namelist[namelist_line][entry] = [tempval]

    # Replace relevant settings
    for domain in range(namelist['domains']['max_dom'][0]):
        log.debug(f'For domain {domain+1}, writing start date variables for {job.start_date}')
        namelist['time_control']['start_year'][domain] = int(job.start_year)
        namelist['time_control']['start_month'][domain] = int(job.start_month)
        namelist['time_control']['start_day'][domain] = int(job.start_day)
        namelist['time_control']['start_hour'][domain] = int(job.start_hour)
        log.debug(f'For domain {domain+1}, writing end date variables for {job.end_date}')
        namelist['time_control']['end_year'][domain] = int(job.end_year)
        namelist['time_control']['end_month'][domain] = int(job.end_month)
        namelist['time_control']['end_day'][domain] = int(job.end_day)
        namelist['time_control']['end_hour'][domain] = int(job.end_hour)

    log.debug('Writing domain-independent time_control variables')
    namelist['time_control']['run_hours'] = int(job.run_hours)
    namelist['time_control']['interval_seconds'] = int(job.input_freq_sec)
    namelist['time_control']['history_interval'] = int(job.output_freq_min)

    log.debug('Writing WRF namelist file')
    f90nml.write(namelist, 'namelist.input')

    return namelist
