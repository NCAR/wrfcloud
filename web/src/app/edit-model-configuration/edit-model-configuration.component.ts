import {Component, Inject, OnInit} from '@angular/core';
import {
  AddModelConfigurationRequest, AddModelConfigurationResponse,
  DeleteModelConfigurationRequest, DeleteModelConfigurationResponse,
  ModelConfiguration, UpdateModelConfigurationRequest,
  UpdateUserResponse
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
   * Get a reference to the PhysicsSuite class so that it can be referenced in the HTML
   */
  public PhysicsSuite: any = PhysicsSuite;


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
   * The WPS namelist parsed as an object
   */
  public wpsNamelist: any = {};


  /**
   * The WRF namelist parsed as an object
   */
  public wrfNamelist: any = {};


  /**
   * A flag to show advanced or basic mode
   */
  public advanced: boolean = false;


  /**
   * Physics suite
   */
  public physicsSuite: string = PhysicsSuite.CONVECTION_PERMITTING;


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

    /* parse namelists */
    this.wpsNamelist = this.parseNamelist(this.modelConfig.wps_namelist);
    this.wrfNamelist = this.parseNamelist(this.modelConfig.wrf_namelist);

    /* set the default physics suite option */
    if (this.modelConfig.wrf_namelist !== '')
    {
      this.physicsSuite = 'custom';
      PhysicsSuite.PRESETS.push(this.physicsSuite);
    }
  }


  /**
   * No action
   */
  ngOnInit(): void
  {
  }


  /**
   * Parse the namelist files into JSON
   */
  public parseNamelist(text: string): Object
  {
    const namelist: any = {'sections': []};

    /* split the string into an array of strings by section */
    const sections: Array<string> = text.split('&');

    /* throw away the first string if it is empty */
    while (sections[0] === '')
      sections.splice(0, 1);

    /* create a section object for each section */
    for (let section of sections)
    {
      const lines: Array<string> = section.split('\n');

      while (lines[0] === '')
        lines.splice(0, 1);

      const sectionName: string = lines.splice(0, 1)[0];
      const values: any = {'names': []};
      namelist['sections'].push(sectionName);
      for (let line of lines)
      {
        /* check for a section terminator */
        if (line.trim().startsWith('/'))
          break;

        /* build the sections name/value pairs */
        const tokens: Array<string> = line.split('=');
        while (tokens[0] === '')
          tokens.splice(0, 1);

        /* if this is not a name=value pair, it is a continuation of the previous value */
        if (tokens.length < 2)
        {
          const lastName: string = values.names[values.names.length - 1];
          values[lastName] += line;
          continue;
        }

        /* parse the name/value pair and add them to the dictionary */
        const name: string = tokens[0].trim();
        const value: string = tokens[1].trim();
        values['names'].push(name);
        values[name] = value;
      }
      namelist[sectionName] = values;
    }

    return namelist;
  }


  /**
   * Go from a namelist object to namelist text
   * @param namelist
   */
  public unparseNamelist(namelist: any): string
  {
    /* initialize an empty string to append */
    let text: string = '';

    /* add each section of the name list */
    for (let section of namelist.sections)
    {
      /* skip empty sections */
      if (section === '')
        continue;

      /* add the section header */
      text += '&' + section + '\n';

      /* add all of the name/value pairs in the section */
      for (let name of namelist[section].names)
        text += '  ' + name + ' = ' + namelist[section][name] + '\n';
      text += '/\n\n';
    }

    return text;
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


  /**
   * Update the physics options based on the newly selected preset name
   *
   * @param presetName See PhysicsSuite.PRESETS
   */
  public updatePhysicsSuite(presetName: string): void
  {
    /* get a physics suite given a preset name */
    const physics: PhysicsSuite = new PhysicsSuite(presetName);

    /* update the namelist object with preset values */
    this.wrfNamelist.physics.mp_physics = physics.mp_physics;
    this.wrfNamelist.physics.cu_physics = physics.cu_physics;
    this.wrfNamelist.physics.ra_lw_physics = physics.ra_lw_physics;
    this.wrfNamelist.physics.ra_sw_physics = physics.ra_sw_physics;
    this.wrfNamelist.physics.bl_pbl_physics = physics.bl_pbl_physics;
    this.wrfNamelist.physics.sf_sfclay_physics = physics.sf_sfclay_physics;
    this.wrfNamelist.physics.sf_surface_physics = physics.sf_surface_physics;

    /* update the namelist text from the updated namelist object */
    this.modelConfig.wrf_namelist = this.unparseNamelist(this.wrfNamelist);

    /* get rid of custom as an option if user selects a preset */
    const customIndex: number = PhysicsSuite.PRESETS.indexOf('custom');
    if (customIndex >= 0)
      PhysicsSuite.PRESETS.splice(customIndex, 1);
  }


  /**
   * Update the namelists when a grid parameter changes
   *
   * @param event see MapAreaSelector gridChange event
   */
  public updateGrid(event: any): void
  {
    /* update the WPS namelist file with new grid parameters */
    this.wpsNamelist.geogrid.map_proj = "'" + event['mapProj'] + "',";
    this.wpsNamelist.geogrid.ref_lat = event['refLat'];
    this.wpsNamelist.geogrid.ref_lon = event['refLon'];
    this.wpsNamelist.geogrid.dx = event['dx'];
    this.wpsNamelist.geogrid.dy = event['dy'];
    this.wpsNamelist.geogrid.e_we = event['e_we'];
    this.wpsNamelist.geogrid.e_sn = event['e_sn'];
    this.wpsNamelist.geogrid.truelat1 = event['refLat'];
    this.wpsNamelist.geogrid.truelat2 = event['refLat'];
    this.wpsNamelist.geogrid.stand_lon = event['refLon'];

    /* update the WRF namelist with new grid parameters */
    this.wrfNamelist.domains.e_we = event['e_we'];
    this.wrfNamelist.domains.e_sn = event['e_sn'];
    this.wrfNamelist.domains.dx = event['dx'];
    this.wrfNamelist.domains.dy = event['dy'];
    this.wrfNamelist.domains.time_step = event['time_step'];

    /* update the namelist text representations from the namelist objects */
    this.modelConfig.wps_namelist = this.unparseNamelist(this.wpsNamelist);
    this.modelConfig.wrf_namelist = this.unparseNamelist(this.wrfNamelist);
  }


  /**
   * Final step to load a file from local disk
   *
   * @param event Contains the file contents
   * @private
   */
  private wpsNamelistLoaded(event: any): void
  {
    /* set as the WPS text */
    this.modelConfig.wps_namelist = event.target.result;
  }


  /**
   * Final step to load a file from local disk
   *
   * @param event Contains the file contents
   * @private
   */
  private wrfNamelistLoaded(event: any): void
  {
    /* set as the WRF text */
    this.modelConfig.wrf_namelist = event.target.result;
  }
}


class PhysicsSuite
{
  /**
   * Preset name for convection-permitting suite
   */
  public static CONVECTION_PERMITTING: string = 'convection-permitting';


  /**
   * Preset name for tropical suite
   */
  public static TROPICAL: string = 'tropical';


  /**
   * List of preset options available
   */
  public static PRESETS: Array<string> = [PhysicsSuite.CONVECTION_PERMITTING, PhysicsSuite.TROPICAL];


  /**
   * Microphysics
   */
  public mp_physics: number;


  /**
   * Cumulus
   */
  public cu_physics: number;


  /**
   * Longwave radiation
   */
  public ra_lw_physics: number;


  /**
   * Shortwave radiation
   */
  public ra_sw_physics: number;


  /**
   * Boundary layer
   */
  public bl_pbl_physics: number;


  /**
   * Surface layer
   */
  public sf_sfclay_physics: number;


  /**
   * Land surface
   */
  public sf_surface_physics: number;


  /**
   * Default constructor
   *
   * @param suite
   */
  constructor(suite: string)
  {
    switch (suite)
    {
      case PhysicsSuite.TROPICAL:
        this.mp_physics = 6;
        this.cu_physics = 16;
        this.ra_lw_physics = 4;
        this.ra_sw_physics = 4;
        this.bl_pbl_physics = 1;
        this.sf_sfclay_physics = 91;
        this.sf_surface_physics = 2;
        break;

      case PhysicsSuite.CONVECTION_PERMITTING:
        this.mp_physics = 8;
        this.cu_physics = 6;
        this.ra_lw_physics = 4;
        this.ra_sw_physics = 4;
        this.bl_pbl_physics = 2;
        this.sf_sfclay_physics = 2;
        this.sf_surface_physics = 2;
        break;

      default:
        this.mp_physics = 8;
        this.cu_physics = 6;
        this.ra_lw_physics = 4;
        this.ra_sw_physics = 4;
        this.bl_pbl_physics = 2;
        this.sf_sfclay_physics = 2;
        this.sf_surface_physics = 2;
        break;
    }
  }
}