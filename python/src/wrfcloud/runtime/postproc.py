"""
Functions for setting up, executing, and monitoring a run of WRF post-processing tasks
"""

import os
from typing import Union
from f90nml import Namelist
from wrfcloud.runtime import RunInfo, Process
from wrfcloud.log import Logger
from wrfcloud.runtime.tools import check_wd_exist
from datetime import datetime, date, timedelta


class PostProc(Process):
    """
    Class for setting up, executing, and monitoring a run of WRF post-processing tasks
    """
    def __init__(self, runinfo: RunInfo):
        """
        Initialize the ProcProc object
        """
        super().__init__()
        self.log = Logger(self.__class__.__name__)
        self.runinfo = runinfo
        self.namelist: Union[None, Namelist] = None

    def get_files(self) -> None:
        """
        Gets all input files necessary for running unipost.exe
        """
        self.log.debug('Linking static files for upp')
        static_files = [ 'parm/hires_micro_lookup.dat',
                         'parm/nam_micro_lookup.dat',
                         'src/lib/g2tmpl/params_grib2_tbl_new' ]

        for statfile in static_files:
            self.symlink(f'{self.runinfo.uppcodedir}/' + statfile, f'{self.runinfo.uppdir}/' + os.path.basename(statfile))

        self.log.debug('Linking control file for upp')
        self.symlink(f'{self.runinfo.uppcodedir}/parm/postxconfig-NT-WRF.txt', f'{self.runinfo.uppdir}/postxconfig-NT.txt')

        self.log.debug('Linking satellite fix files for upp')
        sat_fix_files = [ 'AerosolCoeff/Big_Endian/AerosolCoeff.bin',
                          'CloudCoeff/Big_Endian/CloudCoeff.bin',
                          'EmisCoeff/IR_Water/Big_Endian/Nalli.IRwater.EmisCoeff.bin',
                          'EmisCoeff/MW_Water/Big_Endian/FASTEM4.MWwater.EmisCoeff.bin',
                          'EmisCoeff/MW_Water/Big_Endian/FASTEM5.MWwater.EmisCoeff.bin',
                          'EmisCoeff/MW_Water/Big_Endian/FASTEM6.MWwater.EmisCoeff.bin',
                          'EmisCoeff/IR_Land/SEcategory/Big_Endian/NPOESS.IRland.EmisCoeff.bin',
                          'EmisCoeff/IR_Snow/SEcategory/Big_Endian/NPOESS.IRsnow.EmisCoeff.bin',
                          'EmisCoeff/IR_Ice/SEcategory/Big_Endian/NPOESS.IRice.EmisCoeff.bin',
                          'SpcCoeff/Big_Endian/imgr_g11.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/imgr_g12.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/imgr_g13.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/imgr_g15.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/imgr_mt1r.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/imgr_mt2.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/imgr_insat3d.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/amsre_aqua.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/tmi_trmm.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/ssmi_f13.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/ssmi_f14.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/ssmi_f15.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/ssmis_f16.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/ssmis_f17.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/ssmis_f18.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/ssmis_f19.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/ssmis_f20.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/seviri_m10.SpcCoeff.bin',
                          'SpcCoeff/Big_Endian/v.seviri_m10.SpcCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/imgr_g11.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/imgr_g12.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/imgr_g13.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/imgr_g15.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/imgr_mt1r.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/imgr_mt2.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/imgr_insat3d.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/amsre_aqua.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/tmi_trmm.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/ssmi_f13.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/ssmi_f14.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/ssmi_f15.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/ssmis_f16.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/ssmis_f17.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/ssmis_f18.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/ssmis_f19.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/ssmis_f20.TauCoeff.bin',
                          'TauCoeff/ODPS/Big_Endian/seviri_m10.TauCoeff.bin' ]

        for fixfile in sat_fix_files:
            self.symlink(f'{self.runinfo.uppcodedir}/src/lib/crtm2/src/fix/' + fixfile, f'{self.runinfo.uppdir}/' + os.path.basename(fixfile))

    def run_upp(self) -> None:
        """
        Executes the unipost.exe program
        """
        self.log.debug('Linking unipost.exe to upp working directory')
        self.symlink(f'{self.runinfo.uppcodedir}/bin/unipost.exe', 'unipost.exe')
        
        # Some sort of loop through fhrs to create itag?
        startdate = self.runinfo.startdate
        print(startdate)
        startdate = datetime.strptime(startdate, '%Y-%m-%d_%H:%M:%S')
        enddate   = self.runinfo.enddate
        enddate   = datetime.strptime(enddate, '%Y-%m-%d_%H:%M:%S')
        out_freq  = self.runinfo.output_freq_sec
        increment = timedelta(seconds=3600)

        thisdate = startdate
        while thisdate <= enddate:
            # Create the itag namelist file for this fhr
            self.log.debug('Creating itag file')
            wrfdate = thisdate.strftime("%Y-%m-%d_%H:%M:%S")
            f = open('itag', "w")
            f.write(f'{self.runinfo.wrfdir}/wrfout_d01_{wrfdate}\n')
            f.write("netcdf\n")
            f.write("grib2\n")
            f.write(thisdate.strftime("%Y-%m-%d_%H:%M:%S"))
            f.write("\nNCAR\n")

            f.close()

            self.log.debug('Executing unipost.exe')
            if self.runinfo.wrfcores == 1:
                upp_cmd = './unipost.exe >& unipost.log'
                os.system(upp_cmd)
            else:
                 self.submit_job('unipost.exe',self.runinfo.wrfcores,'wrf')

            thisdate = thisdate + increment

    def run(self) -> bool:
        """
        Main routine that sets up, runs, and monitors post-processing end-to-end
        """
        self.log.info(f'Setting up post-processing for "{self.runinfo.name}"')
        self.log.warn(f"{__name__} isn't fully implemented yet!")

        # Check if experiment working directory already exists, take action based on value of runinfo.exists
        action = check_wd_exist(self.runinfo.exists,self.runinfo.uppdir)
        if action == "skip":
            return True

        os.mkdir(self.runinfo.uppdir)
        os.chdir(self.runinfo.uppdir)

        self.log.debug('Calling get_files')
        self.get_files()

        self.log.debug('Calling run_upp')
        self.run_upp()

        # TODO: Check for successful completion of postproc
        return True
