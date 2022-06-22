import {Component} from '@angular/core';
import {Router} from "@angular/router";


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
   * Flag to tell us if we are logged in or not
   */
  public loggedIn: boolean = false;


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
   */
  constructor(public router: Router)
  {
    /* store a reference to the singleton object */
    AppComponent.singleton = this;

    /* set the menu options based on current user status */
    this.buildMenu();
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
    this.routeTo(this.menuOptions[0].route);
  }


  /**
   * Route to the currently selected page when initialization is finished
   */
  public ngOnInit(): void
  {
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
