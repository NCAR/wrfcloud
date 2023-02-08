"""
Functions for setting up and creating namelist.wps
"""

import f90nml
from f90nml.namelist import Namelist
from wrfcloud.jobs import WrfJob
from wrfcloud.log import Logger


def make_wps_namelist(job: WrfJob, namelist_file: str = None) -> Namelist:
    """
    setup and create the namelist.wps file
    :param job: WRF Job details
    :param namelist_file: Full path to the template namelist file
    """
    log = Logger()
    log.debug(f'Setting up WPS namelist for "{job.job_id}"')

    if namelist_file is None:
        namelist_file = f'{job.static_dir}/namelist.wps'

    with open(namelist_file, encoding='utf-8') as namelist_file_read:
        namelist = f90nml.read(namelist_file_read)

    # convert strings to lists of strings (makes iterating easier)
    for namelist_line in namelist:
        for entry in namelist[namelist_line]:
            if type(namelist[namelist_line][entry]) is str:
                tmp = namelist[namelist_line][entry]
                namelist[namelist_line][entry] = [tmp]

    # replace relevant settings
    for domain in range(namelist['share']['max_dom']):
        log.debug(f'For domain {domain+1}, writing start date {job.start_date}')
        namelist['share']['start_date'][domain] = job.start_date
        log.debug(f'For domain {domain+1}, writing end date {job.end_date}')
        namelist['share']['end_date'][domain] = job.end_date

    log.debug('Writing WPS namelist file')
    f90nml.write(namelist, 'namelist.wps')

    return namelist
