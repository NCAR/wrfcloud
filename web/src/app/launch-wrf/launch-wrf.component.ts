import {Component, OnInit} from '@angular/core';
import {ListModelConfigurationsResponse, RunWrfRequest, RunWrfResponse} from "../client-api";
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
  public busy: boolean = true;


  /**
   * Flag to indicate a successful API response was received
   */
  public success: boolean = false;


  /**
   * Progress bar value for submitting the WRF job
   */
  public submitProgress: number = 40;


  /* request to send the API */
  public req: RunWrfRequest = {
    job_name: '',
    configuration_name: '',
    start_time: 0,
    forecast_length: 86400,
    output_frequency: 3600,
    notify: true
  };

  /* selected index for output frequency option */
  public outputFrequencyIndex: number = 2;

  /* start time represented as a date to be added to the request before sending */
  public start_time = LaunchWrfComponent.getDefaultStartTime();

  /* cycle hour to be added to the request before sending */
  public cycleHour: number = 0;

  /* list of valid cycle hour options */
  public cycleHourOptions = [0, 6, 12, 18];

  /* list of valid output frequency options */
  public outputFrequencyOptions: number[] = [900, 1800, 3600, 10800, 21600, 43200, 86400];

  /* list of valid model configuration options */
  public modelConfigOptions: Array<string> = [];


  constructor()
  {
    this.refreshModelConfigurations();
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
    this.startSubmitProgress();

    /* set the cycle hour on the selected date */
    this.start_time.hours(this.cycleHour);
    this.start_time.minutes(0);
    this.start_time.seconds(0);
    this.start_time.milliseconds(0);

    /* set the start time in the request */
    this.req.start_time = this.start_time.unix();

    /* set the output frequency value */
    this.req.output_frequency = this.outputFrequencyOptions[this.outputFrequencyIndex];

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
    setTimeout(this.app.routeTo.bind(this.app), 1250, '/jobs');
  }


  /**
   * Convert the number of seconds to hours for a slider label
   * @param seconds
   * @param full include full unit labels or just hour value
   */
  public secondsToHoursLabel(seconds: number, full: boolean = false): string
  {
    const hours: number = Math.trunc(seconds / 3600);
    const minutes: number = Math.round((seconds - (hours * 3600)) / 60);
    let label: string;

    if (!full)
    {
      label = hours + '';
      label += minutes > 0 ? (':' + minutes) : '';
    }
    else
    {
      label = hours > 0 ? hours + ' hours' : '';
      label += minutes > 0 ? (minutes + ' minutes') : '';
    }

    return label;
  }


  /**
   * Convert seconds from an array index
   * @param index
   * @param full
   */
  public secondsToHoursLabelOutFreq(index: number, full: boolean = false): string
  {
    const seconds: number = this.outputFrequencyOptions[index];
    return this.secondsToHoursLabel(seconds, full);
  }


  /**
   * Start the progress bar for N seconds
   * @param seconds
   */
  private startSubmitProgress(seconds: number = 30): void
  {
    this.submitProgress = 0;
    this.runSubmitProgress(seconds);
  }


  /**
   * Run the progress bar
   * @param seconds Complete in this many seconds
   * @private
   */
  private runSubmitProgress(seconds: number = 30): void
  {
    const increment: number = 100 / (seconds * 2);
    this.submitProgress += increment;

    if (this.submitProgress < 100 && this.busy)
      setTimeout(this.runSubmitProgress.bind(this), 1000, seconds);
  }


  public refreshModelConfigurations(): void
  {
    this.app.api.sendListModelConfigurations({}, this.handleModelConfigurationResponse.bind(this));
  }


  public handleModelConfigurationResponse(response: ListModelConfigurationsResponse): void
  {
    /* handle errors */
    if (!response.ok)
    {
      this.app.showErrorDialog(response.errors);
      return;
    }

    /* load up model configurations names */
    this.modelConfigOptions = [];
    for (let config of response.data.model_configs)
      this.modelConfigOptions[this.modelConfigOptions.length] = config.name;

    /* select the first one in the list */
    if (this.modelConfigOptions.length > 0)
      this.req.configuration_name = this.modelConfigOptions[0];
  }
}
