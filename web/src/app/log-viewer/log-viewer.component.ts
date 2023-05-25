import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";
import {Pipe, PipeTransform} from '@angular/core';
import {FlatTreeControl} from '@angular/cdk/tree';
import {MatTreeFlatDataSource, MatTreeFlattener} from '@angular/material/tree';
import {
  ListLogsResponse, ListLogsRequest,
  GetLogRequest, GetLogResponse,
  LogNode, ExampleFlatNode
} from "../client-api";
import {AppComponent} from "../app.component";

// @Pipe({name: 'get_log_path'})
// export class LogPathPipe implements PipeTransform {
//   transform(value: LogNode) {
//     return value.name + "/" +
//   }
// }

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

  public treeControl = new FlatTreeControl<ExampleFlatNode>(
      node => node.level,
      node => node.expandable,
  );

  private _transformer = (node: LogNode, level: number) => {
    return {
      expandable: !!node.children && node.children.length > 0,
      name: node.name,
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

  public hasChild = (_: number, node: ExampleFlatNode) => node.expandable;

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
   * Update list of available log files in menu
   * @private
   */
  private updateLogList(log_tree: Array<LogNode>): void
  {
    this.logFiles = {};
    for (let log_app of log_tree) {
      if (log_app.children !== undefined) {
        for (let log_file of log_app.children) {
          let log_path = log_app.name + "/" + log_file.name;
          this.logFiles[log_path] = "";
        }
      }
    }
    this.dataSource.data = log_tree;
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
      this.updateLogList(response.data.log_tree);
  }
}
