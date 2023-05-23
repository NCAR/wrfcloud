import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";
/*import {MatToolbarModule} from '@angular/material/toolbar';*/
import {
  ListLogsResponse,
  ListLogsRequest,
  GetLogRequest,
  GetLogResponse, LogInfo,
} from "../client-api";
import {AppComponent} from "../app.component";
import {MatTableDataSource} from "@angular/material/table";

@Component({
  selector: 'app-log-viewer',
  templateUrl: './log-viewer.component.html',
  styleUrls: ['./log-viewer.component.sass'],
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
   * Table data
   */
  public dataSource: MatTableDataSource<LogInfo> = new MatTableDataSource<LogInfo>([]);

  /**
   * Column names to display on a desktop computer
   */
  public desktopColumns: Array<string> = ['log_name'];


  /**
   * Column names to display on a mobile device
   */
  public mobileColumns: Array<string> = ['log_name'];

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
    let log_infos = [];
    for (let log_filename of log_filenames) {
      this.logFiles[log_filename] = "";
      let log_info = {['log_name']: log_filename};
      log_infos.push(log_info);
    }
    this.dataSource.data = log_infos;
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
