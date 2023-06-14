**************************
Frequently Asked Questions
**************************

  .. dropdown:: How much does it cost?

     The main costs include hosting a web domain, compute cluster time, and data egress. The web domain typically costs $12/year.
     The forecasts are run on AWS's hpc6a clusters, that cost $3.00/hour. The total cost of running a forecast depends on the forecast details. For example, a domain with 500x700 grid points and 6km resolution, 24-hour forecast with hourly output costs about $XX.xx.
     The data egress costs $0.09/gb and the total cost depends on the interaction with the forecast viewer. For example, to view every variable available right now, for a 24-hour forecast with hourly output, it's about 700mb, which translates to about $0.06.


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
     
