import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";
import {FlatTreeControl} from '@angular/cdk/tree';
import {MatTreeFlatDataSource, MatTreeFlattener} from '@angular/material/tree';
import {
  ListLogsResponse, ListLogsRequest,
  GetLogRequest, GetLogResponse,
  LogNode, LogFlatNode
} from "../client-api";
import {AppComponent} from "../app.component";

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

  public treeControl = new FlatTreeControl<LogFlatNode>(
      node => node.level,
      node => node.expandable,
  );

  private _transformer = (node: LogNode, level: number) => {
    return {
      expandable: !!node.children && node.children.length > 0,
      name: node.name,
      full_name: node.full_name,
      level: level,
    };
  };

  public treeFlattener = new MatTreeFlattener(
      this._transformer,
      node => node.level,
      node => node.expandable,
      node => node.children,
  );

  /**
   * Table data
   */
  public dataSource = new MatTreeFlatDataSource(this.treeControl, this.treeFlattener);

  public hasChild = (_: number, node: LogFlatNode) => node.expandable;

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
    // only get log contents from API if it has not already been read
    // otherwise just update the display with log file contents
    if(this.logFiles[this.selectedLogFile].length === 0)
      this.openLog(this.selectedLogFile);
    else
      this.logContent = this.logFiles[this.selectedLogFile];
  }


  /**
   * Update text shown in log content display
   * @private
   */
  public setAndUpdateLogFile(node: LogNode): void
  {
    if (node.full_name === undefined)
      return;
    this.selectedLogFile = node.full_name;
    this.updateLogContent();
  }
  /**
   * Update list of available log files in menu
   * @private
   */
  private updateLogList(log_tree: Array<LogNode>): void
  {
    this.dataSource.data = log_tree;

    this.logFiles = {};
    for (let log_app of log_tree) {
      // find top level logs that have a full name defined
      if (log_app.full_name !== undefined)
        this.logFiles[log_app.full_name] = "";

      // loop through children if any are defined
      if (log_app.children === undefined)
        continue

      for (let log_file of log_app.children) {
        if (log_file.full_name !== undefined)
          this.logFiles[log_file.full_name] = "";
      }
    }
  }

  public listLogs(): void
  {
    this.busy = true;
    const req: ListLogsRequest = {job_id: this.data.job_id};
    this.app.api.sendListLogsRequest(req, this.handleListLogsResponse.bind(this));
  }

  public handleListLogsResponse(response: ListLogsResponse): void
  {
    this.busy = false;
    if (!response.ok)
      this.app.showErrorDialog(response.errors);
    else
      this.updateLogList(response.data.log_tree);
  }

  public openLog(log_filename: string): void
  {
    this.busy = true;
    this.logContent = 'Loading log...';
    const req: GetLogRequest = {job_id: this.data.job_id, log_file: log_filename};
    this.app.api.sendGetLogRequest(req, this.handleGetLogResponse.bind(this));
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
}
