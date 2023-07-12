**************************
Frequently Asked Questions
**************************

  .. dropdown:: How much does it cost?

     The main costs include hosting a web domain, compute cluster time, and data egress. The web domain typically costs $12/year.
     The forecasts are run on AWS's hpc6a clusters, that cost $3.00/hour. The total cost of running a forecast depends on the forecast details. For example, a domain with 500x700 grid points and 6km resolution, 24-hour forecast with hourly output costs about $XX.xx.
     The data egress costs $0.09/GB and the total cost depends on the interaction with the forecast viewer. For example, to view every variable available right now, for a 24-hour forecast with hourly output, it's about 700MB, which translates to about $0.06.

     To give users a general idea of the range of costs, here are some example forecasts and their associated costs for compute. Note that these estimates are for completeing the forecast, the bulk of which happens on the compute nodes, i.e. the most expensive part of the system. Additional costs for tasks like viewing products are generally minimal and are described above. 

     .. list-table:: Forecast cost examples
        :widths: 25 25 50
        :header-rows: 1

        * - Name
          - Resolution
          - Grid Size
          - Projection
          - Physics Suite
          - Forecast Length (hrs)
          - Output Frequency (hrs)
          - Model wall clock (hr)
          - Number of cores 
          - Cost Estimate
          - Post-processing Time (hrs)
          - Total Time (hrs)
        * - Caribbean
          - 6 km
          - 700x500
          - Mercator 
          - Tropical
          - 24
          - 1
          - 2.17
          - 96
          - $6.91
          - 2.45
          - 4.62
        * - Brazil 
          - 3 km
          - 500x520
          - Lambert
          - Conv-permitting
          - 24
          - 1
          - 1.62
          - 96
          - $5.11
          - 1.53
          - 3.15
        * - Denver
          - 1 km
          - 250x250
          - Lambert
          - Conv-permitting
          - 24
          - 1
          - 1.53
          - 48
          - $4.71
          - 0.63
          - 2.17

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
     
