#!/usr/bin/env python3

"""
Functions for setting up and creating namelist.wps
"""

import f90nml
from f90nml.namelist import Namelist
from wrfcloud.runtime import RunInfo
from wrfcloud.log import Logger


def make_wps_namelist(runinfo: RunInfo, nml_file: str = None) -> Namelist:
    """Main routine that sets up and creates namelist.wps"""
    log = Logger()
    log.debug(f'Setting up WPS namelist for "{runinfo.name}"')

    if nml_file is None:
        nml_file = runinfo.staticdir + '/namelist.wps'

    with open(nml_file, encoding='utf-8') as nml_file_read:
        nml = f90nml.read(nml_file_read)

    # Convert strings to lists of strings (makes iterating easier)
    for subnml in nml:
        for entry in nml[subnml]:
            if type(nml[subnml][entry]) is str:
                tempstring = nml[subnml][entry]
                nml[subnml][entry] = [tempstring]

    # Replace relevant settings
    for domain in range(nml['share']['max_dom']):
        log.debug(f'For domain {domain+1}, writing start date {runinfo.startdate}')
        nml['share']['start_date'][domain] = runinfo.startdate
        log.debug(f'For domain {domain+1}, writing end date {runinfo.enddate}')
        nml['share']['end_date'][domain] = runinfo.enddate

    log.debug('Writing WPS namelist file')
    f90nml.write(nml, 'namelist.wps')

    return nml
