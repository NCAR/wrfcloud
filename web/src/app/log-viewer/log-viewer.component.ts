import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";
import {
  GetLogFilesResponse,
  GetLogFilesRequest,
  OpenLogFileRequest,
  OpenLogFileResponse, WrfJob
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
  public logFiles: {[log_filename: string]: string} = {'fake/log_filename.txt': "some fake file content", 'other/log_fakename.txt': "some content for another fake file file"};

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

    this.getLogFiles();
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
    this.logContent = this.logFiles[this.selectedLogFile];
  }


  /**
   * Update list of available log files in menu
   * @private
   */
  private updateLogList(log_filenames: Array<string>): void
  {
    for (let log_filename of log_filenames) {
      this.logFiles[log_filename] = "";
    }
  }


  public openLog(log_filename: string): void
  {
    this.busy = true;
    const req: OpenLogFileRequest = {job_id: this.data.job_id, log_file: log_filename};
    this.app.api.sendOpenLogFileRequest(req, this.handleOpenLogFileResponse.bind(this));
  }


  public getLogFiles(): void
  {
    this.busy = true;
    const req: GetLogFilesRequest = {job_id: this.data.job_id};
    console.log(req);
    this.app.api.sendGetLogFilesRequest(req, this.handleGetLogFilesResponse.bind(this));
  }


  public handleOpenLogFileResponse(response: OpenLogFileResponse): void
  {
    this.busy = false;
    if (!response.ok)
      this.app.showErrorDialog(response.errors);
    else
      this.logFiles[this.selectedLogFile] = response.data.log_content;
  }

  public handleGetLogFilesResponse(response: GetLogFilesResponse): void
  {
    this.busy = false;
    if (!response.ok)
      this.app.showErrorDialog(response.errors);
    else
      this.updateLogList(response.data.log_filenames);
  }
}
