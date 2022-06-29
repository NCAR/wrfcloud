import {Component} from '@angular/core';
import {Router} from "@angular/router";
import {WrfCloudApi} from "./wrfcloud-api";
import {HttpClient} from "@angular/common/http";


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
   * Reference to the API object
   */
  public api: WrfCloudApi;


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
   * Default constructor grabs the singleton instance
   *
   * @param router Inject the angular router
   * @param http Inject the angular http client
   */
  constructor(public router: Router, public http: HttpClient)
  {
    /* store a reference to the singleton object */
    AppComponent.singleton = this;

    /* create the API */
    this.api = new WrfCloudApi(http);

    /* set the menu options based on current user status */
    this.buildMenu();
  }


  /**
   * Route to the currently selected page when initialization is finished
   */
  public ngOnInit(): void
  {
  }


  /**
   * Build the menu options based on user status (e.g., logged in, role, etc)
   * @private
   */
  private buildMenu(): void
  {
    this.menuOptions = [
      {title: 'Run WRF', route: 'launch', icon: 'queue'},
      {title: 'WRF Jobs', route: 'jobs', icon: 'view_list'},
      {title: 'Manage Users', route: 'users', icon: 'account_circle'},
      {title: 'Preferences', route: 'prefs', icon: 'settings'}
    ];
    if (!this.api.loggedIn)
      this.routeTo('login');
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
   * Perform an action if the key pressed is enter
   *
   * @param event Key press event
   * @param action The function to call if the key press is enter
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

    /* route to the login page again */
    this.routeTo('login');
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
