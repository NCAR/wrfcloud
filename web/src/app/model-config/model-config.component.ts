import {Component, OnInit, ViewChild} from '@angular/core';
import {AppComponent} from "../app.component";
import {ListModelConfigurationsResponse, ModelConfiguration} from "../client-api";
import {MatTableDataSource} from "@angular/material/table";
import {MatDialog} from "@angular/material/dialog";
import {MatSort} from "@angular/material/sort";
import {MatPaginator} from "@angular/material/paginator";
import {EditModelConfigurationComponent} from "../edit-model-configuration/edit-model-configuration.component";

@Component({
  selector: 'app-model-config',
  templateUrl: './model-config.component.html',
  styleUrls: ['./model-config.component.sass']
})
export class ModelConfigComponent implements OnInit
{
  // @ts-ignore
  @ViewChild(MatSort) sort: MatSort;
  // @ts-ignore
  @ViewChild(MatPaginator) paginator: MatPaginator;


  /**
   * Application singleton
   */
  public app: AppComponent;


  /**
   * Search filter for the data table
   */
  public filter: string = '';


  /**
   * Indicates loading data from API
   */
  public busy: boolean = false;


  /**
   * List of model configurations
   */
  public modelConfigs: Array<ModelConfiguration> = [];


  /**
   * Table data
   */
  public dataSource: MatTableDataSource<ModelConfiguration> = new MatTableDataSource<ModelConfiguration>([]);


  /**
   * Column names to display on a desktop computer
   */
  public desktopColumns: Array<string> = ['config_name'];


  /**
   * Column names to display on a mobile device
   */
  public mobileColumns: Array<string> = ['config_name'];


  /**
   * Refresh data
   */
  constructor(public dialog: MatDialog)
  {
    /* get the application singleton */
    this.app = AppComponent.singleton;

    /* load a list of model configurations */
    this.loadModelConfigList();
  }


  /**
   *
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
   * Load a list of model configurations from the server
   */
  public loadModelConfigList(): void
  {
    this.busy = true;
    this.app.api.sendListModelConfigurations({}, this.handleModelConfigListResponse.bind(this));
  }


  /**
   * Handle a response from list model configurations
   * @param response
   */
  public handleModelConfigListResponse(response: ListModelConfigurationsResponse): void
  {
    this.busy = false;

    if (response.ok)
    {
      /* save the model configuration list */
      this.modelConfigs = response.data.model_configs;
      this.dataSource.data = this.modelConfigs;
    }
    else
    {
      /* show errors */
      // TODO: Add this back once API works: this.app.showErrorDialog(response.errors);
    }
  }


  /**
   * Handle an event where the user clicks on a row in the table
   *
   * @param modelConfig ModelConfiguration object for the row clicked
   */
  public rowClicked(modelConfig: ModelConfiguration): void
  {
    const editData: {modelConfig: ModelConfiguration, edit: boolean} = {
      modelConfig: modelConfig,
      edit: true
    };

    this.dialog.open(EditModelConfigurationComponent, {data: editData}).afterClosed().subscribe(
      () => { this.loadModelConfigList(); }
    );
  }


  /**
   * Apply the search filter to the table items
   */
  public filterModified(): void
  {
    this.dataSource.filter = this.filter;
  }


  /**
   * Add a new model configuration
   */
  public addModelConfig(): void
  {
    const editData: {modelConfig: ModelConfiguration, edit: boolean} = {
      modelConfig: {id: '', name: '', description: '', model_name: 'wrf', cores: 0, wps_namelist: '', wrf_namelist: ''},
      edit: false
    };

    this.dialog.open(EditModelConfigurationComponent, {data: editData}).afterClosed().subscribe(
      () => { this.loadModelConfigList(); }
    );
  }
}
