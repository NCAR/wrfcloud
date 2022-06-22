import {Component} from '@angular/core';
import {Router} from "@angular/router";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.sass']
})
export class AppComponent
{
  public static singleton: AppComponent;


  public menuOptions = [
    {title: 'Manage Users', route: 'users'},
    {title: 'Run WRF', route: 'launch'},
    {title: 'WRF Jobs', route: 'jobs'},
    {title: 'Preferences', route: 'prefs'}
  ];


  constructor(public router: Router)
  {
    AppComponent.singleton = this;
  }


  public routeTo(route: string): void
  {
    this.router.navigateByUrl('/' + route);
  }

}
