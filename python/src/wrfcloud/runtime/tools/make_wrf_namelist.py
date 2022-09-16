#!/usr/bin/env python3

"""
Functions for setting up and creating namelist.input
"""

import f90nml
from f90nml.namelist import Namelist
from wrfcloud.runtime import RunInfo
from wrfcloud.log import Logger


def make_wrf_namelist(runinfo: RunInfo, nml_file: str = None) -> Namelist:
    """Main routine that sets up and creates namelist.input"""
    log = Logger()
    log.debug(f'Setting up WRF namelist for "{runinfo.name}"')

    if nml_file is None:
        nml_file = runinfo.staticdir + '/namelist.input'

    with open(nml_file, encoding='utf-8') as nml_file_read:
        nml = f90nml.read(nml_file_read)

    # Convert singlet values to lists of values (makes iterating easier)
    for subnml in nml:
        for entry in nml[subnml]:
            if isinstance(nml[subnml][entry], (str, int, float, complex)):
                tempval = nml[subnml][entry]
                nml[subnml][entry] = [tempval]

    # Replace relevant settings
    for domain in range(nml['domains']['max_dom'][0]):
        log.debug(f'For domain {domain+1}, writing start date variables for {runinfo.startdate}')
        print(f"{nml['time_control']['start_year'][domain]=}")
        print(f'{runinfo.startyear=}')
        nml['time_control']['start_year'][domain] = int(runinfo.startyear)
        nml['time_control']['start_month'][domain] = int(runinfo.startmonth)
        nml['time_control']['start_day'][domain] = int(runinfo.startday)
        nml['time_control']['start_hour'][domain] = int(runinfo.starthour)
        log.debug(f'For domain {domain+1}, writing end date variables for {runinfo.enddate}')
        nml['time_control']['end_year'][domain] = int(runinfo.endyear)
        nml['time_control']['end_month'][domain] = int(runinfo.endmonth)
        nml['time_control']['end_day'][domain] = int(runinfo.endday)
        nml['time_control']['end_hour'][domain] = int(runinfo.endhour)

    log.debug(f'Writing domain-independent time_control variables')
    nml['time_control']['run_hours'] = int(runinfo.runhours)
    nml['time_control']['interval_seconds'] = int(runinfo.input_freq_sec)
    nml['time_control']['history_interval'] = int(runinfo.output_freq_min)

    log.debug(f'Writing WRF namelist file')
    f90nml.write(nml, 'namelist.input')

    return nml
