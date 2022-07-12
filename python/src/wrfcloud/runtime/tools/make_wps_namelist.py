#!/usr/bin/env python3

"""
Functions for setting up and creating namelist.wps
"""

import f90nml

def make_wps_namelist(runinfo, logger, nml_file=None):
    """Main routine that sets up and creates namelist.wps"""
    logger.debug(f'Setting up WPS namelist for "{runinfo.name}"')

    if nml_file is None:
        nml_file = runinfo.topdir + '/domains/test/namelist.wps'

    with open(nml_file, encoding='utf-8') as nml_file_read:
        nml = f90nml.read(nml_file_read)
    #Replace relevant settings
    for domain in range(nml['share']['max_dom']):
        nml['share']['start_date'][domain] = runinfo.startdate
        nml['share']['end_date'][domain] = runinfo.enddate

    logger.debug(f'Writing WPS namelist file to {runinfo.wd}')
    f90nml.write(nml, 'namelist.wps')
