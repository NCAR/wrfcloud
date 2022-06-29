import {Component, OnInit} from '@angular/core';
import {AppComponent} from "../app.component";

@Component({
  selector: 'app-logout',
  templateUrl: './logout.component.html',
  styleUrls: ['./logout.component.sass']
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
