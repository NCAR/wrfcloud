import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";
import {
  ListLogsResponse,
  ListLogsRequest,
  GetLogRequest,
  GetLogResponse, WrfJob
} from "../client-api";
import {AppComponent} from "../app.component";

@Component({
  selector: 'app-log-viewer',
  templateUrl: './log-viewer.component.html',
  styleUrls: ['./log-viewer.component.sass']
})
export class LogViewerComponent implements OnInit
{
  /**
   * Reference to the application singleton
   */
  public app: AppComponent;

  public job_id: string = "";
  /**
   * Content of log file to display
   */
  public logFiles: {[log_filename: string]: string} = {'Loading Logs...': ""};

  public selectedLogFile: string = "";

  public logContent: string = "";

  /**
   * Note which action we are performing
   */
  public action: string = '';


  /**
   * Flag the dialog as busy or not (i.e., waiting for API response)
   */
  public busy: boolean = false;


  /**
   * Default constructor
   *
   * @param dialogRef
   * @param data Contains the full job object and the edit flag
   */
  constructor(public dialogRef: MatDialogRef<LogViewerComponent>, @Inject(MAT_DIALOG_DATA) public data: {job_id: string})
  {
    /* get a reference to the application singleton */
    this.app = AppComponent.singleton;

    this.listLogs();
  }


  ngOnInit(): void
  {
  }

  /**
   * Update text shown in log content display
   * @private
   */
  public updateLogContent(): void
  {
    this.openLog(this.selectedLogFile);
  }


  /**
   * Update list of available log files in menu
   * @private
   */
  private updateLogList(log_filenames: Array<string>): void
  {
    this.logFiles = {};
    for (let log_filename of log_filenames) {
      this.logFiles[log_filename] = "";
    }
  }


  public openLog(log_filename: string): void
  {
    this.busy = true;
    const req: GetLogRequest = {job_id: this.data.job_id, log_file: log_filename};
    this.app.api.sendGetLogRequest(req, this.handleGetLogResponse.bind(this));
  }


  public listLogs(): void
  {
    this.busy = true;
    const req: ListLogsRequest = {job_id: this.data.job_id};
    this.app.api.sendListLogsRequest(req, this.handleListLogsResponse.bind(this));
  }


  public handleGetLogResponse(response: GetLogResponse): void
  {
    this.busy = false;
    if (!response.ok)
      this.app.showErrorDialog(response.errors);
    else {
      this.logFiles[this.selectedLogFile] = response.data.log_content;
      this.logContent = this.logFiles[this.selectedLogFile];
    }
  }

  public handleListLogsResponse(response: ListLogsResponse): void
  {
    this.busy = false;
    if (!response.ok)
      this.app.showErrorDialog(response.errors);
    else
      this.updateLogList(response.data.log_filenames);
  }
}
