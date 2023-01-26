import {Component} from '@angular/core';
import {Router} from "@angular/router";
import {User, WhoAmIResponse, ClientApi, WrfMetaDataConfiguration, GetWrfMetaDataResponse, GetWrfMetaDataRequest} from "./client-api";
import {HttpClient} from "@angular/common/http";
import {MatDialog} from "@angular/material/dialog";
import {ErrorDialogComponent} from "./error-dialog/error-dialog.component";


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.sass']
})
export class AppComponent
{
  /**
   * AppComponent singleton
   */
  public static singleton: AppComponent;


  /**
   * Switch to mobile view on screens smaller than this
   */
  public mobileWidthBreakpoint: number = 840;


  /**
   * Mobile screen size flag
   */
  public isMobile: boolean = window.innerWidth < this.mobileWidthBreakpoint;


  /**
   * Reference to the API object
   */
  public api: ClientApi;


  /**
   * List of menu options to render the menus
   */
  public menuOptions: Array<MenuOption> = [
    {title: '', route: '', icon: ''}
  ];


  /**
   * Tracks the currently selected page
   */
  public currentPage: string = this.menuOptions[0].route;


  /**
   * Information of currently logged-in user
   */
  public user: User|undefined;


  /**
   * WRF meta data
   */
  public wrfMetaData: Array<WrfMetaDataConfiguration>|undefined;


  /**
   * Default constructor grabs the singleton instance
   *
   * @param router Inject the angular router
   * @param http Inject the angular http client
   * @param dialog Inject the angular material dialog
   */
  constructor(public router: Router, public http: HttpClient, public dialog: MatDialog)
  {
    /* store a reference to the singleton object */
    AppComponent.singleton = this;

    /* create the API */
    this.api = new ClientApi(http);
  }


  /**
   * Route to the currently selected page when initialization is finished
   */
  public ngOnInit(): void
  {
    /* set the menu options based on current user status */
    this.buildMenu();
  }


  /**
   * The window was resized -- update for mobile/tablet/desktop
   */
  public windowResized(event: any): void
  {
    this.isMobile = event.target.innerWidth < this.mobileWidthBreakpoint;
  }


  /**
   * Get only the active menu options (not placeholders)
   * @return List of menu options
   */
  public getActiveMenuOptions(): Array<MenuOption>
  {
    const activeOptions: Array<MenuOption> = [];
    for (let option of this.menuOptions)
      if (option.title !== '')
        activeOptions[activeOptions.length] = option;

    return activeOptions;
  }


  /**
   * Build the menu options based on user status (e.g., logged in, role, etc)
   * @private
   */
  public buildMenu(): void
  {
    /* if not logged in, clear the menu options and send to login page*/
    if (!this.api.loggedIn)
    {
      this.menuOptions = [
        {title: '', route: 'login', icon: ''},
        {title: '', route: '', icon: ''},
        {title: '', route: '', icon: ''},
        {title: '', route: '', icon: ''}
      ];
    }

    /* make sure we have user info */
    else if (this.user === undefined)
    {
      this.refreshUserData();
      setTimeout(this.buildMenu.bind(this), 250);
      return;
    }

    /* add actions for readonly user */
    else if (this.user!.role_id === 'readonly')
    {
      this.menuOptions = [
        {title: 'WRF Jobs', route: 'jobs', icon: 'view_list'},
        {title: 'Preferences', route: 'prefs', icon: 'settings'},
        {title: '', route: '', icon: ''},
        {title: '', route: '', icon: ''}
      ];
    }

    /* add actions for regular user */
    else if (this.user!.role_id === 'regular')
    {
      this.menuOptions = [
        {title: 'Run WRF', route: 'launch', icon: 'queue'},
        {title: 'WRF Jobs', route: 'jobs', icon: 'view_list'},
        {title: 'Preferences', route: 'prefs', icon: 'settings'},
        {title: '', route: '', icon: ''}
      ];
    }

    /* add actions for regular user */
    else if (this.user!.role_id === 'maintainer')
    {
      this.menuOptions = [
        {title: 'Run WRF', route: 'launch', icon: 'queue'},
        {title: 'WRF Configs', route: 'configs', icon: 'satellite'},
        {title: 'WRF Jobs', route: 'jobs', icon: 'view_list'},
        {title: 'Preferences', route: 'prefs', icon: 'settings'}
      ];
    }

    /* add actions for regular user */
    else if (this.user!.role_id === 'admin')
    {
      this.menuOptions = [
        {title: 'Run WRF', route: 'launch', icon: 'queue'},
        {title: 'WRF Configs', route: 'configs', icon: 'satellite'},
        {title: 'WRF Jobs', route: 'jobs', icon: 'view_list'},
        {title: 'Manage Users', route: 'users', icon: 'account_circle'},
        {title: 'Preferences', route: 'prefs', icon: 'settings'}
      ];
    }

    /* route to an appropriate screen */
    if (this.router.url === '/' || this.router.url === '/activate' || this.router.url === '/reset' || this.router.url === '/configs')
      return;  /* do not interfere with these routes for anonymous users */
    else if (this.user !== undefined && (this.router.url.startsWith('/view') || this.router.url.startsWith('/jobs')))
      return;  /* do not interfere with these routes for authenticated users */
    else if (this.menuOptions.length === 0)
      this.routeTo('login');
    else
      this.routeTo(this.menuOptions[0].route);
  }


  /**
   * Set the route value
   *
   * @param path Name of the path to switch to
   */
  public routeTo(path: string): void
  {
    this.currentPage = path;
    const ignore = this.router.navigateByUrl('/' + path);
  }


  /**
   * Perform an action if the key pressed is 'enter'
   *
   * @param event Key press event
   * @param action The function to call if the key press is 'enter'
   */
  public onEnter(event: any, action: Function): void
  {
    if (event.keyCode === 13)
      action();
  }


  /**
   * Logout the user
   */
  public logout(): void
  {
    /* clear the credentials */
    if (this.api.loggedIn)
      this.api.logout();

    /* rebuild the menu options */
    this.buildMenu();
  }


  /**
   * Show the errors from a response message
   */
  public showErrorDialog(errors: Array<string>|undefined): void
  {
    /* Add a general message if there are no errors in the list */
    if (errors === undefined)
      errors = ['An unknown error occurred'];

    /* open the dialog and show the errors */
    this.dialog.open(ErrorDialogComponent, {data: errors});
  }


  /**
   * Query the server for user data
   */
  public refreshUserData(): void
  {
    this.api.sendWhoAmIRequest(this.handleUserDataResponse.bind(this));
  }


  /**
   *  Handle a user data response
   *
   * @param response
   */
  public handleUserDataResponse(response: WhoAmIResponse): void
  {
    this.user = response.ok ? response.data.user : undefined;
  }
}


/**
 * Define a MenuOption type
 */
export interface MenuOption
{
  title: string;
  route: string;
  icon: string;
}
