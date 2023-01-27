import {Component, Inject, OnInit} from '@angular/core';
import {
  CreateUserResponse,
  DeleteUserResponse, ModelConfiguration,
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
  public autoCoreCount: boolean = true;


  /**
   * A flag to tell us if we are editing an existing user or creating a new one
   */
  public edit: boolean;


  /**
   * A flag to tell us if we are editing an existing user or creating a new one
   */
  public create: boolean;


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
  }


  /**
   * Handle a response
   *
   * @param response
   */
  public handleDeleteModelConfigurationResponse(response: DeleteUserResponse): void
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
  }


  /**
   * Handle a response
   *
   * @param response
   */
  public handleCreateModelConfigurationResponse(response: CreateUserResponse): void
  {
    this.busy = false;

    if (response.ok)
      this.dialogRef.close();
    else
      this.app.showErrorDialog(response.errors);
  }


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

  public formatCores(event: any): string
  {
    console.log(event);
    return 'DODO';
  }

  public round(val: number): number
  {
    return Math.round(val * 100) / 100;
  }
}
