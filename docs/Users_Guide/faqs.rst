**************************
Frequently Asked Questions
**************************

  .. dropdown:: How much does it cost?

     The main costs include hosting a web domain, compute cluster time, and data egress. The web domain typically costs $12/year.
     The forecasts are run on AWS's hpc6a clusters, that cost $3.00/hour. The total cost of running a forecast depends on the forecast details. For example, a domain with 500x700 grid points and 6km resolution, 24-hour forecast with hourly output costs about $XX.xx.
     The data egress costs $0.09/GB and the total cost depends on the interaction with the forecast viewer. For example, to view every variable available right now, for a 24-hour forecast with hourly output, it's about 700MB, which translates to about $0.06.

     To give users a general idea of the range of costs, here are some example forecasts and their associated costs for compute. Note that these estimates are for completeing the forecast, the bulk of which happens on the compute nodes, i.e. the most expensive part of the system. Additional costs for tasks like viewing products are generally minimal and are described above. 

     +----------+---+-------+-----+----+-------+-----+------+
     | Name     |Res|Grid   |Fcst |Out |Wall   |Cores|Cost  |
     |          |   |Size   |Len  |Freq|Clock  |     |      |
     +==========+===+=======+=====+====+=======+=====+======+
     | Caribbean|6km|700x500|24 hr|1 hr|2.17 hr|96   |$6.91 |
     +----------+---+-------+-----+----+-------+-----+------+
     |  Brail   |3km|500x520|24 hr|1 hr|1.62 hr|96   |$5.11 |
     +----------+---+-------+-----+----+-------+-----+------+
     |  Denver  |1km|250x250|24 hr|1 hr|1.53 hr|48   |$4.71 |
     +----------+---+-------+-----+----+-------+-----+------+

  .. dropdown:: Can you run multiple domains?

     Currently we support running single domains only. Multiple domains are on the list for future enhancements. 

  .. dropdown:: What is the input data used? 

     Initial conditions are provided by the Global Forecasting System (GFS) at 3-hourly time intervals. Future enhancements may allows for 1-hourly interval data to be used. 

  .. dropdown:: Can the input data source be changed?

     No, at this time the system only uses the Global Forecasting System (GFS) for initial conditions. But future enhancements could allow for varying sources.

  .. dropdown:: Can you download the model output?

     At this time, the model data is not saved. Only the forecast plots viewable on the Forecast Viewer are saved. But, we expect to include the option to save model output in the next released version.

  .. dropdown:: What cloud service providers are supported?

     Currently the system only works on Amazon Web Services (AWS). Interested in porting it to another CSP? We are too! Let’s talk, send us an email.
     
  .. dropdown:: What model is used?

     The system is currently designed to use the WRF model.
    
  .. dropdown:: A WRF job failed, how do I fix it?

     WRF jobs can fail for many reasons. First, look at the log files for the failed job on the WRF Jobs page. The status of the job may help indicate which component the job failed on, e.g. metgrid, or real, or wrf, so you can search those log files first for a clues as to what went wrong. If the job is based off a new configuration (i.e. model domain, physics, etc.), it's possible those settings aren't properly tuned. There are countless ways to create new model configurations and requires some knowledge of WRF and NWP modeling. See `WRF documentation <https://www2.mmm.ucar.edu/wrf/users/docs/user_guide_v4/v4.4/contents.html>`_ for help. But, some common errors you may encounter include:

     * Over-decomposition: The error "domain size is too small for this many processors" or something similar may appear in the rsl.* files and the real step will fail. This means that too many processors were used for the domain size. If you used the autocompute core count when creating your configuration, it's possible it over-estimated. Go back to your configuration and edit it, uncheck the autocompute core option, and manually set it to something smaller. Then try to run a forecast again with that updated configuration.
     * CFS errors: "cfl" errors may occur in the WRF rsl.* log files. This means the model became unstable which can happen for a lot of reasons and often requires some advanced debugging. The `WRF Forum <https://forum.mmm.ucar.edu/>`_ may have some clues. 
