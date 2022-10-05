.. _overview:

*********************
Overview of WRF Cloud 
*********************

Purpose and organization of the User's Guide
============================================

The goal of this User's Guide is to document the procedures required to install the WRF Cloud system and to serve as a reference for using and adapting the system to an organization's own needs. 

UCAR/UCP/COMET and UCAR/NCAR/RAL
================================

This project is made possible through funding by `UCAR <https://www.ucar.edu/>`_/`UCP <https://www.ucar.edu/community-programs>`_/`COMET <https://www.comet.ucar.edu/>`_ and collaborations with `UCAR <https://www.ucar.edu/>`_/`NCAR <https://ncar.ucar.edu/>`_/`RAL <https://ral.ucar.edu/>`_/`MMM <https://www.mmm.ucar.edu/>`_.  

.. _wrfcloud-goals:

WRF Cloud goals and design philosophy
=====================================

The WRF Cloud framework is a cloud-based forecasting system that was designed to facilitate cost-efficent forecasts motivated by the need to enable access of a state-of-the-art numerical weather prediction system to communities that lack the computational resources. Flexibility is at the forefront of all design choices of the framework, with the understanding that for under-resourced communities, the wants versus needs may compete and often change. For example, when launching a forecast, users have the option to choose to run a cloud configuration that is fast but more expensive, or slower but cheaper, providing opportunity to weigh the cost versus benefits for any given weather situation or budget constraints. In addition, the system is built to allow for future enhancements to be incorporated with relative ease. Establishing a framework that is flexible and circumvents much of the current computational resource limitations affords local officials the ability to prepare for and respond to weather-related events promptly and effectively. It also lays the foundation to further NWP development and earth system prediction, for example by incorporating additional verification techniques and new observations. A streamlined and practical approach is achieved by using a serverless design philosophy including an intuitive user interface and responsive website that allows the end user to launch and view forecasts from any device with an internet connection. The control of the forecast configuration and forecast output graphics are both incorporated into the same website, which allows the user a one-stop-shop to launch and view a forecast. This opens opportunities for on-demand rapid deployment of the system to produce forecasts in preparation of or in response to natural disasters, from the field on a mobile device or on a personal laptop; the only requirement being an internet connection. The framework can also be used as a regular forecasting tool with automated forecast cycles customized to the needs of a community.


WRF Cloud components
====================

The WRF Cloud system consists primarily of one python package that was developed to orchestrate all components of the end-to-end system leveraging serverless architure principals. Amazon Web Services (AWS) is used for the cloud service provider and several AWS resources are used to construct the entire system. The weather forecast itself is produced using initial conditions from the Global Forecast System (GFS) to run the Weather Research and Modeling (`WRF <https://www2.mmm.ucar.edu/wrf/users/>`_) system, including it's pre-processor WPS. The WRF model output is post-processed using the Unified Post Processor (`UPP <https://dtcenter.org/community-code/unified-post-processor-upp>`_) and from there the data are processed for plotting and served up to the system's website. 

System overview
---------------

.. _overview-figure:

.. figure:: figure/overview-figure.png

NWP Overview (schematic of NWP?)
--------------------------------

.. _release-notes:

.. include:: release-notes.rst

Future development plans
========================

New features are being considered for the next release. These may include:

* Verification capabilities
* Enhanced User Interface plotting features
* New plot types, e.g. vertical cross sections and Skew T - Log P plots
* Increased customizabilitiy of configuration 

Code support
============

At this time, support beyond the contents of this User's Guide is available through established collaborations only. Please contact `COMET <https://www.comet.ucar.edu/form/contact>`_ for further inquiries. 
