import {Component, OnInit} from '@angular/core';
import {AppComponent} from "../app";

@Component({
    selector: 'app-home',
    templateUrl: './home.html',
    styleUrls: ['./home.sass'],
    standalone: false
})
export class HomeComponent implements OnInit
{
  public app: AppComponent;


  constructor()
  {
    this.app = AppComponent.singleton;
  }


  ngOnInit(): void
  {
    if (this.app.user !== undefined && this.app.api.loggedIn)
      this.app.routeTo('/jobs');
    else
      this.app.routeTo('/login');
  }
}
