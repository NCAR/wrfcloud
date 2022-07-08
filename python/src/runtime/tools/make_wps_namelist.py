#!/usr/bin/env python3

"""
Functions for setting up and creating namelist.wps
"""

import logging
import f90nml

def make_wps_namelist(runinfo, logger, nml_file='domains/test/namelist.wps'):
    """Main routine that sets up and creates namelist.wps"""
    logger.debug(f'Setting up WPS namelist for "{runinfo.name}"')

    with open(nml_file) as nml_file_read:
        nml = f90nml.read(nml_file_read)
    #Replace relevant settings
    print(nml['share']['max_dom'])
    for domain in range(nml['share']['max_dom']):
        nml['share']['start_date'][domain] = runinfo.startdate
        nml['share']['end_date'][domain] = runinfo.enddate

    logger.debug(f'Writing WPS namelist file to {runinfo.wd}')
    f90nml.write(nml, runinfo.wd + '/namelist.wps')

