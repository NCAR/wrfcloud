import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";
import {ApiResponse, CancelDeleteJobRequest, WrfJob} from "../client-api";
import {AppComponent} from "../app.component";

@Component({
  selector: 'app-job-details',
  templateUrl: './job-details.component.html',
  styleUrls: ['./job-details.component.sass']
})
export class JobDetailsComponent implements OnInit
{
  /**
   * Reference to the application singleton
   */
  public app: AppComponent;


  /**
   * Convert status codes to text
   */
  public statusCodeToText: Array<String> = [
    'Pending', 'Starting', 'Running', 'Finished', 'Canceled', 'Failed'
  ];


  /**
   * List of job information attributes to display
   */
  public info: Array<{name: String, value: String}> = [];


  /**
   * Allow the job to be deleted
   */
  public allowDelete: boolean = false;


  /**
   * Allow the job to be canceled
   */
  public allowCancel: boolean = false;


  /**
   * Allow the job viewer to be opened
   */
  public allowOpen: boolean = false;


  /**
   * Flag the dialog as busy or not (i.e., waiting for API response)
   */
  public busy: boolean = false;


  /**
   * Note which action we are performing
   */
  public action: string = '';


  /**
   * Default constructor
   *
   * @param dialogRef
   * @param data Contains the full job object and the edit flag
   */
  constructor(public dialogRef: MatDialogRef<JobDetailsComponent>, @Inject(MAT_DIALOG_DATA) public data: {job: WrfJob, edit: boolean})
  {
    /* get a reference to the application singleton */
    this.app = AppComponent.singleton;

    this.updateButtons();

    this.info[this.info.length] = {name: 'Created By', value: data.job.user_email};
    this.info[this.info.length] = {name: 'Configuration Name', value: data.job.configuration_name};
    this.info[this.info.length] = {name: 'Job Name', value: data.job.job_name};
    this.info[this.info.length] = {name: 'Start Date', value: data.job.start_date};
    this.info[this.info.length] = {name: 'End Date', value: data.job.end_date};
    this.info[this.info.length] = {name: 'Forecast Length', value: (data.job.forecast_length / 3600) + ' hours'};
    this.info[this.info.length] = {name: 'Output Frequency', value: (data.job.output_frequency / 3600) + ' hours'};
    this.info[this.info.length] = {name: 'Notify On Complete', value: data.job.notify ? 'Enabled' : 'Disabled'};
    this.info[this.info.length] = {name: 'Job Progress', value: (data.job.progress * 100) + '%'};
    this.info[this.info.length] = {name: 'Job Status', value: this.statusCodeToText[data.job.status_code]};
    this.info[this.info.length] = {name: 'Status Message', value: data.job.status_message};
    if (data.job.error_logs != null) {
      this.info[this.info.length] = {name: 'Error Logs', value: data.job.error_logs};
    }
  }


  ngOnInit(): void
  {
  }


  /**
   * Decide which buttons should be visible or hidden
   * @private
   */
  private updateButtons(): void
  {
    const sc: number = this.data.job.status_code;
    this.allowCancel = sc >= 0 && sc <= 2;  // pending, starting, running
    this.allowDelete = sc >= 3 && sc <= 5;  // finished, canceled, failed
    this.allowOpen = sc === 3;              // finished
  }


  public cancelJob(): void
  {
    this.busy = true;
    this.action = 'cancel';
    const req: CancelDeleteJobRequest = {job_id: this.data.job.job_id};
    this.app.api.sendCancelJobRequest(req, this.responseHandler.bind(this));
  }


  public deleteJob(): void
  {
    this.busy = true;
    this.action = 'delete';
    const req: CancelDeleteJobRequest = {job_id: this.data.job.job_id};
    this.app.api.sendDeleteJobRequest(req, this.responseHandler.bind(this));
  }


  public openJob(): void
  {
    this.app.routeTo('/view/' + this.data.job.job_id);
    this.closeDialog();
  }


  public responseHandler(response: ApiResponse): void
  {
    this.busy = false;
    if (!response.ok)
      this.app.showErrorDialog(response.errors);
    else if (this.action === 'delete')
      this.closeDialog();
    else if (this.action === 'cancel')
    {
      this.data.job.status_code = 4;
      this.updateButtons();
    }
  }


  public closeDialog(): void
  {
    this.dialogRef.close();
  }
}
