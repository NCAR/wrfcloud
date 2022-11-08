import {Component, OnInit} from '@angular/core';
import {RunWrfRequest} from "../client-api";

@Component({
  selector: 'app-launch-wrf',
  templateUrl: './launch-wrf.component.html',
  styleUrls: ['./launch-wrf.component.sass']
})
export class LaunchWrfComponent implements OnInit
{
  req: RunWrfRequest = {
    job_name: '',
    configuration_name: 'test',
    start_time: LaunchWrfComponent.getDefaultStartTime(),
    forecast_length: 86400,
    output_frequency: 3600,
    notify: true
  };


  constructor()
  {
  }


  ngOnInit(): void
  {
  }


  /**
   * Get the default start time (before now rounded to 6 hours)
   */
  public static getDefaultStartTime(): number
  {
    const now: number = new Date().getTime() / 1000;
    const rounded: number = Math.round(now / 21600) * 21600;

    return rounded;
  }
}
