import {Component, OnInit} from '@angular/core';
import {AppComponent} from "../app.component";

@Component({
  selector: 'app-view-jobs',
  templateUrl: './view-jobs.component.html',
  styleUrls: ['./view-jobs.component.sass']
})
export class ViewJobsComponent implements OnInit
{
  /**
   * Reference to the app singleton
   */
  public app: AppComponent;


  constructor()
  {
    this.app = AppComponent.singleton;
  }


  ngOnInit(): void
  {
  }
}
