import {Component, OnInit} from '@angular/core';
import {AppComponent} from "../app";

@Component({
    selector: 'app-logout',
    templateUrl: './logout.html',
    styleUrls: ['./logout.sass'],
    standalone: false
})
export class LogoutComponent implements OnInit
{
  /**
   * Reference to the application singleton
   */
  public app: AppComponent;


  /**
   * Get a reference to the application singleton
   */
  constructor()
  {
    this.app = AppComponent.singleton;
  }


  /**
   * Logout when display is ready
   */
  ngOnInit(): void
  {
    this.app.logout();
  }
}
