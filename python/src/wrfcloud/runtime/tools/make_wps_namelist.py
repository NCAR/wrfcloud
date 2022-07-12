#!/usr/bin/env python3

"""
Functions for setting up and creating namelist.wps
"""

import f90nml

def make_wps_namelist(runinfo, logger, nml_file=None):
    """Main routine that sets up and creates namelist.wps"""
    logger.debug(f'Setting up WPS namelist for "{runinfo.name}"')

    if nml_file is None:
        nml_file = runinfo.staticdir + '/namelist.wps'

    with open(nml_file, encoding='utf-8') as nml_file_read:
        nml = f90nml.read(nml_file_read)

    #Convert strings to lists of strings (makes iterating easier)
    for subnml in nml:
        for entry in nml[subnml]:
            if type(nml[subnml][entry]) is str:
                tempstring = nml[subnml][entry]
                nml[subnml][entry] = [ tempstring ]

    #Replace relevant settings
    for domain in range(nml['share']['max_dom']):
        logger.debug(f'For domain {domain+1}, writing {runinfo.startdate}')
        nml['share']['start_date'][domain] = runinfo.startdate
        nml['share']['end_date'][domain] = runinfo.enddate

    logger.debug(f'Writing WPS namelist file to {runinfo.wd}')
    f90nml.write(nml, 'namelist.wps')

    return nml
