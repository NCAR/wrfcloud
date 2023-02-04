import {AfterViewInit, Component, OnDestroy, OnInit, ViewChild} from '@angular/core';
import {AppComponent} from "../app.component";
import {
  JobStatusResponse,
  WrfJob,
  ListJobResponse,
  WebsocketListener,
  WebsocketMessage,
} from "../client-api";
import {MatSort} from "@angular/material/sort";
import {MatPaginator} from "@angular/material/paginator";
import {MatTableDataSource} from "@angular/material/table";

@Component({
  selector: 'app-view-jobs',
  templateUrl: './view-jobs.component.html',
  styleUrls: ['./view-jobs.component.sass']
})
export class ViewJobsComponent implements OnInit, AfterViewInit, OnDestroy, WebsocketListener
{
  // @ts-ignore
  @ViewChild(MatSort) sort: MatSort;
  // @ts-ignore
  @ViewChild(MatPaginator) paginator: MatPaginator;

  /**
   * Reference to the app singleton
   */
  public app: AppComponent;


  /**
   * A list of WRF jobs in the system
   */
  public jobs: WrfJob[] = [];


  /**
   * Table data
   */
  public dataSource: MatTableDataSource<WrfJob> = new MatTableDataSource<WrfJob>([]);


  /**
   * Search filter for the data table
   */
  public filter: string = '';


  /**
   * Flag to indicate loading data from the API
   */
  public busy: boolean = false;


  /**
   * Flag to indicate an active websocket connection to receive job status updates
   */
  public subscribed: boolean = false;


  /**
   * Flag to indicate this object is being destroyed
   * @private
   */
  private destructing: boolean = false;


  /**
   * Column names to display on a desktop computer
   */
  public desktopColumns: Array<string> = ['job_id', 'job_name', 'configuration_name', 'cycle_time', 'forecast_length', 'status'];


  /**
   * Column names to display on a mobile device
   */
  public mobileColumns: Array<string> = ['job_id', 'cycle_time', 'status'];


  /**
   * Default constructor
   */
  constructor()
  {
    /* get a reference to the application singleton */
    this.app = AppComponent.singleton;

    /* refresh job data from the API */
    this.refreshJobData();
    this.app.api.connectWebsocket(this);
  }


  /**
   * Angular initializer
   */
  ngOnInit(): void
  {
  }


  /**
   * Grab the table paginator and sorter
   */
  ngAfterViewInit()
  {
    this.dataSource.sort = this.sort;
    this.dataSource.paginator = this.paginator;
  }


  /**
   * Clean up when this object goes away
   */
  ngOnDestroy()
  {
    /* close the websocket when we are not looking at this page */
    this.destructing = true;
    this.app.api.disconnectWebsocket();
  }


  /**
   * Query the server for job data
   */
  public refreshJobData(): void
  {
    /* start the busy spinner */
    this.busy = true;

    /* load the job data */
    this.app.api.sendListJobsRequest({}, this.handleJobDataResponse.bind(this));
  }


  /**
   * Handle a job list response
   *
   * @param response
   */
  public handleJobDataResponse(response: ListJobResponse): void
  {
    /* stop the busy spinner */
    this.busy = false;

    /* handle the response */
    if (response.ok)
    {
      this.jobs = response.data.jobs;
      this.dataSource.data = this.jobs;
    }
    else
    {
      this.app.showErrorDialog(response.errors);
    }
  }


  /**
   * Handle an event where the user clicks on a row in the table
   *
   * @param job Job object for the row clicked
   */
  public jobClicked(job: WrfJob): void
  {
    // TODO: Open dialog to view all job details or delete/cancel job;
  }


  /**
   * Apply the search filter to the table items
   */
  public filterModified(): void
  {
    this.dataSource.filter = this.filter;
  }


  public websocketOpen(event: Event): void
  {
    /* subscribe to job status changes */
    console.log('websocket subscribe');
    this.subscribed = this.app.api.subscribeToJobChanges();
  }


  public websocketClose(event: CloseEvent): void
  {
    /* connect again if we get disconnected */
    console.log('websocket closed');
    this.subscribed = false;
    if (!this.destructing)
      this.app.api.connectWebsocket(this);
  }


  public websocketMessage(event: MessageEvent): void
  {
    /* parse the websocket message -- must be valid JSON */
    const data: WebsocketMessage = JSON.parse(event.data);

    /* handle the message */
    switch(data.type)
    {
      case 'JobStatus':
        this.handleJobStatusMessage(data.data as JobStatusResponse);
        break;
    }
  }


  /**
   *
   * @param message The
   * @private
   */
  private handleJobStatusMessage(message: JobStatusResponse)
  {
    /* extract the job from the message */
    const job: WrfJob = message.data.job;

    /* find the job in the table */
    for (let job_ of this.jobs)
    {
      if (job_.job_id === job.job_id)
      {
        job_.status_code = job.status_code;
        job_.status_message = job.status_message;
        job_.job_name = job.job_name;
        job_.output_frequency = job.output_frequency;
        job_.forecast_length = job.forecast_length;
        job_.configuration_name = job.configuration_name;
        job_.start_date = job.start_date;
        job_.end_date = job.end_date;
        job_.progress = job.progress;
        job_.user_email = job.user_email;
        job_.notify = job.notify;
        job_.layers = job.layers;
        job_.domain_center = job.domain_center;
      }
    }
  }
}
