import {Component, Inject, OnInit} from '@angular/core';
import {
  AddModelConfigurationRequest, AddModelConfigurationResponse,
  CreateUserResponse, DeleteModelConfigurationRequest, DeleteModelConfigurationResponse,
  DeleteUserResponse, ModelConfiguration, UpdateModelConfigurationRequest,
  UpdateUserResponse,
} from "../client-api";
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";
import {AppComponent} from "../app.component";

@Component({
  selector: 'app-edit-model-configuration',
  templateUrl: './edit-model-configuration.component.html',
  styleUrls: ['./edit-model-configuration.component.sass']
})
export class EditModelConfigurationComponent implements OnInit
{
  /**
   * Available role options
   */
  public roles: any = [
    {value: 'readonly', displayName: 'Read-only'},
    {value: 'regular', displayName: 'Regular'},
    {value: 'admin', displayName: 'Admin'}
  ];


  /**
   * Busy flag
   */
  public busy: boolean = false;


  /**
   * Application singleton
   */
  public app: AppComponent;


  /**
   * User to edit
   */
  public modelConfig: ModelConfiguration;


  /**
   * Option to automatically decide the core count
   */
  public autoCoreCount: boolean = false;


  /**
   * A flag to tell us if we are editing an existing user or creating a new one
   */
  public edit: boolean;


  /**
   * A flag to tell us if we are editing an existing user or creating a new one
   */
  public create: boolean;


  /**
   * Show a hint for the configuration name
   */
  public showNameHint: boolean = false;


  /**
   * Copy data into the user object
   *
   * @param dialogRef
   * @param data
   */
  constructor(public dialogRef: MatDialogRef<EditModelConfigurationComponent>, @Inject(MAT_DIALOG_DATA) public data: {modelConfig: ModelConfiguration, edit: boolean})
  {
    /* get singleton */
    this.app = AppComponent.singleton;

    /* deep copy */
    this.modelConfig = JSON.parse(JSON.stringify(data.modelConfig));
    this.autoCoreCount = this.modelConfig.cores === 0;

    /* set the edit/create flag */
    this.edit = data.edit;
    this.create = !this.edit;
  }


  ngOnInit(): void
  {
  }


  /**
   * Submit the user updates to the server
   */
  public updateModelConfiguration(): void
  {
    /* start the spinner */
    this.busy = true;

    /* domain center and size should be computed on the server-side */
    if (this.modelConfig.hasOwnProperty('domain_center'))
      delete this.modelConfig['domain_center'];
    if (this.modelConfig.hasOwnProperty('domain_size'))
      delete this.modelConfig['domain_size'];
    if (this.autoCoreCount)
      this.modelConfig.cores = 0;

    /* send the update request to the API */
    const requestData: UpdateModelConfigurationRequest = {
      model_config: this.modelConfig
    };
    this.app.api.sendUpdateModelConfiguration(requestData, this.handleUpdateModelConfigurationResponse.bind(this));
  }


  /**
   * Duplicate the configuration
   */
  public duplicateModelConfiguration(): void
  {
    this.create = true;
    this.edit = false;
    this.modelConfig.name = this.modelConfig.name + '_copy';
  }


  /**
   * Handle a response
   *
   * @param response
   */
  public handleUpdateModelConfigurationResponse(response: UpdateUserResponse): void
  {
    this.busy = false;

    if (response.ok)
      this.dialogRef.close();
    else
      this.app.showErrorDialog(response.errors);
  }


  /**
   * Delete a user from the system
   */
  public deleteModelConfiguration(): void
  {
    /* start the spinner */
    this.busy = true;

    /* send an API request to delete the configuration */
    const requestData: DeleteModelConfigurationRequest = {
      configuration_name: this.modelConfig.name
    };
    this.app.api.sendDeleteModelConfiguration(requestData, this.handleDeleteModelConfigurationResponse.bind(this));
  }


  /**
   * Handle a response
   *
   * @param response
   */
  public handleDeleteModelConfigurationResponse(response: DeleteModelConfigurationResponse): void
  {
    this.busy = false;

    if (response.ok)
      this.dialogRef.close();
    else
      this.app.showErrorDialog(response.errors);
  }


  /**
   * Create a new user in the system
   */
  public createModelConfiguration(): void
  {
    /* start the spinner */
    this.busy = true;

    /* domain center and size should be computed on the server-side */
    if (this.modelConfig.hasOwnProperty('domain_center'))
      delete this.modelConfig['domain_center'];
    if (this.modelConfig.hasOwnProperty('domain_center'))
      delete this.modelConfig['domain_center'];

    /* send an API request to add the configuration */
    const requestData: AddModelConfigurationRequest = {model_config: this.modelConfig};
    this.app.api.sendAddModelConfiguration(requestData, this.handleCreateModelConfigurationResponse.bind(this));
  }


  /**
   * Handle a response
   *
   * @param response
   */
  public handleCreateModelConfigurationResponse(response: AddModelConfigurationResponse): void
  {
    /* stop the spinner */
    this.busy = false;

    /* handle the response */
    if (response.ok)
      this.dialogRef.close();
    else
      this.app.showErrorDialog(response.errors);
  }


  /**
   * Load a namelist file from local disk
   * @param type
   */
  public loadNamelistFile(type: 'wrf'|'wps'): void
  {
    /* trigger the hidden file input element */
    const fileInput = document.getElementById(type + '-namelist-file');
    if (fileInput !== undefined && fileInput !== null)
      fileInput.click();
  }


  /**
   *
   * @param event
   * @param type Either WPS or WRF
   */
  public fileSelected(event: any, type: 'wrf'|'wps'): void
  {
    /* get the file name */
    const file = event.target.files[0];

    /* create a new reader and set up the load listener */
    const fileReader = new FileReader();
    console.log(type);
    const loadHandler = type === 'wrf' ?
      this.wrfNamelistLoaded.bind(this) :
      this.wpsNamelistLoaded.bind(this);
    fileReader.addEventListener('load', loadHandler);

    /* read the file -- call handler when ready */
    fileReader.readAsText(file);
  }


  /**
   * Validate the configuration name as the user types
   */
  public validateConfigName(): void
  {
    /* alphanumeric, dashes, and underscores only */
    const matches: Array<String>|null = this.modelConfig.name.match(/^[a-zA-Z0-9_-]+/)
    if (matches && matches.length > 0)
      if (matches[0].length === this.modelConfig.name.length)
      {
        this.showNameHint = false;
        return;
      }
    this.showNameHint = true;
  }


  private wpsNamelistLoaded(event: any): void
  {
    /* set as the WPS text */
    this.modelConfig.wps_namelist = event.target.result;
  }

  private wrfNamelistLoaded(event: any): void
  {
    /* set as the WRF text */
    this.modelConfig.wrf_namelist = event.target.result;
  }

  public round(val: number): number
  {
    return Math.round(val * 100) / 100;
  }
}
