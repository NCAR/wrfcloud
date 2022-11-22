import {Component, OnInit} from '@angular/core';
import {AppComponent} from "../app.component";

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.sass']
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
