import {AfterViewInit, Component, OnDestroy, OnInit, ViewChild} from '@angular/core';
import {AppComponent} from "../app.component";
import {Job, ListJobResponse, WebsocketListener} from "../client-api";
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
  public jobs: Job[] = [];


  /**
   * Table data
   */
  public dataSource: MatTableDataSource<Job> = new MatTableDataSource<Job>([]);


  /**
   * Search filter for the data table
   */
  public filter: string = '';


  /**
   * Flag to indicate loading data from the API
   */
  public busy: boolean = false;


  /**
   * Column names to display on a desktop computer
   */
  public desktopColumns: Array<string> = ['job_id', 'configuration_name', 'cycle_time', 'forecast_length', 'status'];


  /**
   * Column names to display on a mobile device
   */
  public mobileColumns: Array<string> = ['job_id', 'cycle_time', 'status'];


  /**
   * Default constructor
   */
  constructor()
  {
    this.app = AppComponent.singleton;
    this.refreshJobData();
    this.app.api.connectWebsocket(this);
  }


  /**
   * On init
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
    this.app.api.sendListJobsRequest(this.handleJobDataResponse.bind(this));
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
  public jobClicked(job: Job): void
  {
    this.app.routeTo('/view/jobid1');
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
    console.log('Websocket Connected On The Viewer Page:');
    console.log(event);
    const subscribed: boolean = this.app.api.subscribeToJobChanges();
    console.log('Subscribed: ' + subscribed);
  }


  public websocketClose(event: CloseEvent): void
  {
    console.log('Websocket Disconnected Leaving the Viewer Page:');
    console.log(event);
  }


  public websocketMessage(event: MessageEvent): void
  {
    console.log('Websocket Message:');
    console.log(event);
  }
}
