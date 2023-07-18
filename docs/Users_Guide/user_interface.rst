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

.. _ui_wrf_configs:

WRF Configs
===========
A model configuration is a combination of user-defined parameters that together define the computational domain, grid extents, projection, resolution, model dynamics and model physics. These parameters are defined in the namelist.wps and namelist.input that are used by WRF to run its forecasts.

The **WRF Configs** page displays a table with all of the model configurations that have been created on your system. Click on any of the model configs to view the model config management described below. If you have not created any configurations yet, the table will be empty. Click the **Add Config** button at the top to create a new configuration. See :ref:`ui_model_config_gui` for more details.

.. _ui_managing_model_configs:

Managing Model Configurations
-----------------------------

Create new config
^^^^^^^^^^^^^^^^^

To create a new model configuration, click on the **Add Config** button on the **WRF Configs** tab.
Type a name for the new model configuration, adjust the settings to create your new domain, then click the **Save** button.
The new configuration will appear in the table on the **WRF Configs** tab.
See :ref:`ui_model_config_gui` for more information about customizing a new model configuration.

Start from an existing config (Duplicate and modify)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also copy an existing configuration and modify it as desired.
Click on the existing configuration in the table on the **WRF Configs** tab to open the **Edit WRF Configuration** window.
Click the **Duplicate** button at the bottom of the window.
The title of the window should change to **Create WRF Configuration** and the *Name* value will change to the original configuration name with *_copy* added to the end.
Edit the settings described in the :ref:`ui_model_config_gui` section.
Be sure to change the Name and Description values.
Click **Save** when finished and the new configuration will appear in the table on the **WRF Configs** tab.

.. _ui_update_existing_config:

Update existing config
^^^^^^^^^^^^^^^^^^^^^^

To update an existing model configuration, click on the configuration name in the table on the **WRF Configs** tab to open the **Edit WRF Configuration** window.
Edit the settings described in the :ref:`ui_model_config_gui` section.
Click the **Update** button to save changes or click **Cancel** to discard changes.

Remove config
^^^^^^^^^^^^^

To permanently remove an existing model configuration, click on the configuration name in the table on the **WRF Configs** tab, then click the orange **Remove** button to delete it.


.. _ui_model_config_gui:

Model Configuration GUI
-----------------------

Model configurations and their corresponding namelist files can be easily created and modified using the model configuration GUI.
See :ref:`ui_managing_model_configs` for information on how to access the GUI.
The model config GUI provides a simple interface to define new domains and configurations.
The sections of the GUI include:

Name
^^^^

Name of the model configuration. This should ideally be a shorter character string, but it is helpful to provide a meaningful name to describe the model configuration details. For example, "6km_caribbean_trop" may be a name given to describe a configuration of the Caribbean Sea with 6km grid spacing that uses the tropical physics suite.

Description
^^^^^^^^^^^
(Optional) Add a description to provide more information about the model configuration.
For a configuration named "6km_caribbean_trop," the description could be "6km Caribbean Domain with standard tropical physics suite".

Users have the option to use the **Basic** editing mode (shown by default) or an **Advanced** editing mode. The **Basic** editing mode allows the user to create the configuration in the GUI without having to edit namelists directly.

Basic
^^^^^

The **Basic** mode information includes:

**Projection:** Choose a projection from the dropdown menu. Options are *Lambert* or *Mercator*.

**Domain Definition:** Use the map tool to draw a box of your regional domain. From a desktop computer, hold the *CTRL* button and drag to draw a new box. The latitude and longitude corners on the right side will automatically adjust based on your box on the map. You may also edit the North, West, South, and East latitude/longitude boxes directly. Changes will be reflected in the box on the map.

**Grid Resolution:** Enter your model resolution in meters.

**Physics Suite:** Select the physics suite option. Options include "tropical", "conv-permitting", or "custom". The custom setting simply means you will edit the physics settings directly in the namelist.input using the Advanced editing mode. The tropical and convection-permitting options reflect what the WRF modeling team provides as a good place to start, which include settings for two typical applications: convection-permitting weather over the contiguous U.S. and tropical storms/convection. Information can be found `here <https://www2.mmm.ucar.edu/wrf/users/physics/wrf_physics_suites.php>`_, but the settings are shown below for quick reference and use in defining a new model configuration.

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

**Core count:** The default is to have "Set automatically" checked. This means the system will determine a good estimate of the number of cores to use based on the grid you defined in your model configuration. You may also uncheck this box and manually select the number of cores. This may come in handy in your job fails with over-decomposition and you need to manually adjust the cores to be smaller.

Advanced
^^^^^^^^

Advanced users may find it helpful to use the **Advanced** editing mode. This tab of the GUI shows the contents of the namelist.wps and namelist.input in an editable window. Users may edit the contents directly. Any edits made to the contents will also be reflected in the **Basic** editing tab, and vice versa. For example, one may use the **Basic** editing mode to create a domain, and the **Advanced** editing mode to update the physics. Additionally, the **Advanced** editing mode allows users to upload existing namelist files directly.

Limitations & Considerations of Model Configuration Options
-----------------------------------------------------------
* Currently the system only supports single domains: *max_dom* must be 1.
* Initialization data is limited to GFS at 3-hour intervals. The available date range is roughly the last 2 years.
* Regional WRF resolutions may range from about 1km to 12km.
* There are many options in WRF. Choosing new configurations requires some knowledge of WRF to be successful. Additional information about these settings can be found in the `WRF Users Guide <https://www2.mmm.ucar.edu/wrf/users/docs/user_guide_v4/v4.4/contents.html>`_.


.. _wrf_jobs:

WRF Jobs 
========

A table of jobs that have been launched can be found in the **WRF Jobs** tab.
The table provides the following information:

* **Job ID:** Unique job ID for the forecast. This is automatically generated by the system and used for advanced debugging.
* **Name:** If a Job Name was provided in the previous step when Launching a new forecast, it will appear in this column. (Note: this is optional)
* **Configuration:** Name of model configuration used for the forecast.
* **Cycle Time:** The initialization date and time of the forecast.
* **Forecast Length:** The total forecast length in hours.
* **Status:** The current status and progress of the forecast. The initial status will say "Launching Cluster" as the system prepares its compute nodes and sets up the forecast. From there, the status will change indicating it's progress through the job, e.g. "Running Ungrib", "Running Metgrid", etc. A completed job will display an **Open Viewer** button that users can click to take them to the forecast viewer for that job. A failed job will display a status message indicating which component has failed, e.g. "Real failed." Errors can be investigated using the the Log Viewer (see below).

Managing a WRF Job
------------------

Each row of the table can be clicked to open a window with additional job information and buttons to manage the job.

**Cancel Job**

An orange **Cancel Job** button will be displayed while a job is running.
Click on this button to stop the job. The job status will change to *Canceled*.
Note that cancelling a job does not delete the job from the system.

**Delete Job**

An orange **Delete Job** button will be displayed for completed or failed jobs.
Click on this button to completely remove all data for the job, including plots on the forecast viewer, from the system.

**Viewer**

A blue **Viewer** button will be displayed for a successful job.
Click on this button to open the forecast viewer for the job.

**Logs**

A blue **Logs** button will be displayed for a successful, failed, or cancelled job.
Click on this button to open the **Log Viewer** window to inspect log files from the system.
A list of log files is displayed on the left hand side.

The first file (wrfcloud-run-W########.log) is the system log file that contains logging messages for each step. This provides a good overview of the progress and steps the system takes from start to finish.

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
