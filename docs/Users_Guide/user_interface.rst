.. _user_interface:

**************
User Interface
**************

Users access the WRF cloud system through a web browser and domain name unique to each organization. In this documentation, app.wrfcloud.com may be used as an example. This website serves as the primary user interface (UI) through which users are able to view, launch, and monitor forecasts as well as manage user accounts, depending on each user's role and corresponding permissions (see System Administration Roles and Permissions :numref:`roles`). Users can navigate the site using the Menu options. The Menu options are described below. 

Homepage
========

The main home pages contains brief information about the system and is an access point to Login to the system.

Login / Logout
--------------

To Login to the system, click on the blue Login button on the Homepage. This will take you to a prompt to enter your Email Address and Password, and then you can click the blue Login button. If your credentials are propoerly validated, you'll be taken to the main system page. Once logged into the system, you can logout by clicking the "Logout" button.

Forgot / Reset password
----------------------- 

If you forgot your password, you an click on the "I forgot my password" button on the Login page. You'll be prompted to enter your email address. Check your email from instructions to reset your password.

.. _run_wrf:

Run WRF
=======

The Run WRF tab is where you can launch a new WRF run. There are several parameters described below that need to be selected in order to setup and launch a new forecast. 

* **Model Confiuration:** Name of the model configuration. The list of available model configurations will appear in the dropdown menu. These are created using the WRF Config Menu option (see below). 
* **Job Name:** This is an optional name to give your run to help describe its purpose or meaning.
* **Cycle Date:** The inital date of the forecast. Select from the calendar or enter manually in MM/DD/YYYY format. (Please see note below)
* **Cyle Hour:** The initial cycle hour. Options are 00, 06, 12, 18 UTC.
* **Forecast Length:** The forecast legnth in hours.
* **Output Frequency:** The frequency of forecast output.

After the parameters are set, check or uncheck the "Notify when finished" box. Then click the Launch button. You will be automatically taken to the WRF Jobs status page after the system initializes the cluster.

.. note::
   The initialization data currently used is the Global Forecasting System (GFS) at 3-hourly intervals. Currently GFS data availability is limited to roughly the last two years. In addition, users running close to real-time cycles should allow a 6-hour buffer to ensure that cycle is available on the server. Data can be retrieved from two sources: NOAA's GFS archive on `AWS's S3 <https://registry.opendata.aws/noaa-gfs-bdp-pds/>`_, and the `NOMADS <https://nomads.ncep.noaa.gov/>`_ server if requeseted data is within 10 days.
   
   Remember that longer forecast length and greater the output frequency, the more the forecast will cost.

.. _wrf_configs:

WRF Configs
===========
A model configuration is a combination of user-defined parameters that together define the computational domain, grid extents and projection, resolution, model dynamics and model physics. These parameters are defined in the namelist.wps and namelist.input that are used by WRF to run its forecasts. 

Configuration Parameters
------------------------
The following information is needed to create a new model configuration:

**Name:** Name of the model configuration. This should ideally be a shorter character string, but it is helpful to provide a meaningful name to describe the model configuration details. For example, "6km_caribbean_trop" may be a name given to describe a configuration of the Caribbean Sea with 6km grid spacing that uses the tropical physics suite.  

**Description:** Additional description to provide more information about the model configuration. In the example above, "6km_caribbean_trop", the description might be "6km Caribbean Domain with standard tropical physics suite". 

**WPS Namelist:** The information contained in namelist.wps. Users will primarily be interested in modifying the &geogrid section of the namelist.wps to customize their region of interest. Note that currently the system only support single domains, so max_dom must be set to 1. Additional information about these settings can be found in the `WRF Users Guide <https://www2.mmm.ucar.edu/wrf/users/docs/user_guide_v4/v4.4/contents.html>`_.

**WRF Namelist:** The information contained in namelist.input. Users will primarily be interested in modifying the &domains section to match their namelist.wps, and &physics section to change physics options. Note that currently the system only support single domains, so max_dom must be set to 1. Additional information about these settings can be found in the `WRF Users Guide <https://www2.mmm.ucar.edu/wrf/users/docs/user_guide_v4/v4.4/contents.html>`_. As quick start, WRF provides two sample physics suites, which include settings for two typical applications: convection-permitting weather over the contiguous U.S. and tropical storms/convection. Information can be found `here <https://www2.mmm.ucar.edu/wrf/users/physics/wrf_physics_suites.php>`_, but the settings are shown below for quick reference and use in defining a new model configuration.

.. list-table:: CONUS convection-permitting suite
   :widths: 10 10 10
   :header-rows: 0
   
   * - Microphysics
     - Thompson
     - mp_physics= 8
   * - Cumulus
     - Tiedtke
     - cu_physics= 6
   * - Longwave radiation
     - RRTMG
     - ra_lw_physics= 4
   * - Shortwave radiation
     - RRTMG
     - ra_sw_physics= 4
   * - Boundary layer
     - MYJ
     - bl_pbl_physics= 2
   * - Surface layer
     - MYJ
     - sf_sfclay_physics= 2
   * - Land surface
     - Noah LSM
     - sf_surface_physics= 2

.. list-table:: tropical weather/convection suite
   :widths: 10 10 10 
   :header-rows: 0
   
   * - Microphysics
     - WSM6
     - mp_physics= 6
   * - Cumulus
     - new Tiedtke
     - cu_physics= 16
   * - Longwave radiation
     - RRTMG
     - ra_lw_physics= 4
   * - Shortwave radiation
     - RRTMG
     - ra_sw_physics= 4
   * - Boundary layer
     - YSU
     - bl_pbl_physics= 1
   * - Surface layer
     - MM5
     - sf_sfclay_physics= 91
   * - Land surface
     - Noah LSM
     - sf_surface_physics= 2
 

**Core Count:** By default the system uses 96 cores. But for smaller or coarser configurations, using too many cores will over-decompose the grid and result in model failure. WRF provides some information in this `FAQ <https://forum.mmm.ucar.edu/threads/how-many-processors-should-i-use-to-run-wrf.5082/>`_ as a guide to set the appropriate number of cores. In the future, this will be automated.


Limitations of Model Configuration Options
------------------------------------------
* Currently the system only supports single domains.
* Initialization data is limited to GFS at a 3-hourly interval and the date range of availability is generally within about the last 2 years.
* Regional WRF resolutions may range from about 1km to 12km.
* There are many options in WRF, choosing new configurations requires some knowledge of WRF to be successful.


Managing Model Configurations
-----------------------------
**Create new config**

To create a new model configuration, users can either do so from scratch or duplicate an existing config and save as new.

Option 1. From scratch:
   Click on the "Add Config" button and the Create WRF Configuration window will pop up. Enter a new name and description. The user can populate the WPS Namelist and WRF Namelist sections by either copy and paste from local file, enter the text manually, or uploading a file from their local computer using the "Load File" button. Set the appropriate number of cores. Then click "Save".
   
Option 2. From existing config (duplicate and save as new):
   As an alternative to avoid needing a local file, users can start with an existing configuration and duplicate it to use it as a guide or template, then modify the settings, and save it as a new model configuration name. To duplicate an existing model configuration, click on the Configuration name and a new Edit window will pop up. Click on the "Duplicate" button and a fresh editing window will appear with a copy of the configuration. You can then enter a new Name, make changes to the namelist, and click save. The new configuration will then appear in your list. 

**Update existing config**

To update an existing model configuration, click on the Configuration name and a new Edit window will pop up. Make the desired changes and click the "Update" button.

**Remove config**

To remove an existing model configuration completely, click on the Configuration name and a new Edit window will pop up. Click the "Remove" button to remove.


.. _wrf_jobs:

WRF Jobs 
========
A table of jobs that have been launched can be found under the WRF Jobs menu option. The table provides the following information:

* **Job ID:** Unique job ID for the forecast. This is automatically generated by the system and used for advanced debugging.
* **Name:** If a Job Name was provided in the previous step when Launching a new forecast, it will appear in this column. (Note: this is optional)
* **Configuration:** Name of model configuration use for the forecast. 
* **Cycle Time:** The initialization date and time of the forecast.
* **Forecast Length:** The total forecast length in hours.
* **Status:** The current status and progress of the forecast. The initial status will say "Launching Cluster" as the system prepares its compute nodes and sets up the forecast. From there, the status will change indicating it's progress through the job, e.g. "Running Ungrib", "Running Metgrid", etc. A completed job will show an "Open Viewer" button that users can click to take them to the forecast viewer for that WRF job. A failed job with show a status inidicating which component it failed on, e.g. "Real failed", and providing a place to look for errors in the Log Viewer (see below).

Managing a WRF Job
------------------
Each row of the table is selectable which will pop up a window with additional job information and helpful buttons to aid in job management described below.

**Cancel a Job**

An orange "Cancel" button will appear that can be used to stop in-progress jobs. The job status will change to Canceled. Note that canceling a job does not delete that job from the system. 

**Delete a Job**

An orange "Delete" button will appear for completed or failed jobs. Clicking this Delete button will result in all data, including plots on the forecast viewer, from that job to be completely removed from the system. 

**View Forecast**

A successful job will have a blue "Viewer" button that users can click on to take them to the forecast viewer for that WRF job.

**View Logs**

A blue "Logs" button is available to easily view log files from the system directly on the user interface. Clicking on the Logs button will pop up a Log View window. A list of log files is available on the left hand side. 

The first file (wrfcloud-run-W########.log) is the system log file and contains logging messages of each step along the way. This gives a good overview of the progress and steps the system takes from start to finish.

Following the system log file, each component of WPS (geogrid, ungrib, metgrid) and WRF (real, wrf) has an expandable menu that lists the component's log files. These log files can be inspected when a job fails to better understand where the problem occurred and how to fix it. Knowledge of WRF is helpful in understanding the contents of these files. 

.. _manage_users:

Manage Users (Admins only)
==========================

For users with Admin privileges, the users of the system can be managed in this menu option. Click on any user name to change their role and permissions or remove from system access. To add new users, click on the "Add user" button and enter their email, Name, and select a role for permissions. (see System Administration Roles and Permissions :numref:`roles`)

.. _preferences:

Preferences 
===========

Users may manage their own preferences in this tab. Currently the only option is to change your password.

.. _forecast_viewer:

Forecast Viewer 
===============

The forecast plots can be accessed by clicking on the Job ID or Status of a run in the WRF Jobs tab. See Graphics page for more information.
