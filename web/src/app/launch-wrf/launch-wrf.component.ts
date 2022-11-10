import {Component, OnInit} from '@angular/core';
import {ApiResponse, RunWrfRequest, RunWrfResponse} from "../client-api";
import {TEXT_ALIGN} from "ol/render/canvas/TextBuilder";
import start = TEXT_ALIGN.start;
import * as moment from 'moment';
import {AppComponent} from "../app.component";

@Component({
  selector: 'app-launch-wrf',
  templateUrl: './launch-wrf.component.html',
  styleUrls: ['./launch-wrf.component.sass']
})
export class LaunchWrfComponent implements OnInit
{
  /* reference to the app singleton */
  public app: AppComponent = AppComponent.singleton;

  /**
   * Flag to indicate we are waiting for the API
   */
  public busy: boolean = false;


  /**
   * Flag to indicate a successful API response was received
   */
  public success: boolean = false;


  /* request to send the API */
  public req: RunWrfRequest = {
    job_name: '',
    configuration_name: 'test',
    start_time: 0,
    forecast_length: 86400,
    output_frequency: 3600,
    notify: true
  };

  /* start time represented as a date to be added to the request before sending */
  public start_time = LaunchWrfComponent.getDefaultStartTime();

  /* cycle hour to be added to the request before sending */
  public cycleHour: number = 0;

  /* list of valid cycle hour options */
  public cycleHourOptions = [0, 6, 12, 18];

  /* list of valid model configuration options */
  public modelConfigOptions = ['test'];


  constructor()
  {
  }


  ngOnInit(): void
  {
  }


  /**
   * Get the default start time (before now rounded to 6 hours)
   */
  public static getDefaultStartTime()
  {
    return moment().utc();
  }

  /**
   *
   */
  public startWrf(): void
  {
    /* start the busy spinner */
    this.busy = true;

    /* set the cycle hour on the selected date */
    this.start_time.hours(this.cycleHour);
    this.start_time.minutes(0);
    this.start_time.seconds(0);
    this.start_time.milliseconds(0);

    /* set the start time in the request */
    this.req.start_time = this.start_time.unix();

    /* send the API request */
    this.app.api.sendLaunchWrf(this.req, this.handleStartWrfResponse.bind(this));
  }


  /**
   * Handle a launch WRF response
   * @param response
   */
  public handleStartWrfResponse(response: RunWrfResponse): void
  {
    /* stop the busy spinner */
    this.busy = false;

    /* show any errors */
    if (!response.ok)
    {
      this.app.showErrorDialog(response.errors);
      return;
    }

    /* show success message and route to the job status page */
    this.success = true;
    setTimeout(this.app.routeTo.bind(this.app), 1500, '/jobs');
  }
}
