import {Component, OnInit} from '@angular/core';
import {AppComponent} from "../app.component";
import {WrfJob, LayerRequest} from "../client-api";
import {Map, View} from 'ol';
import TileLayer from 'ol/layer/Tile';
import {OSM} from 'ol/source';
import {MatSliderChange} from "@angular/material/slider";
import {useGeographic} from "ol/proj";

@Component({
  selector: 'app-wrf-viewer',
  templateUrl: './wrf-viewer.component.html',
  styleUrls: ['./wrf-viewer.component.sass']
})
export class WrfViewerComponent implements OnInit
{
  /**
   * Singleton viewer component
   */
  public static singleton: WrfViewerComponent;


  /**
   * App singleton object
   */
  public app: AppComponent;


  /**
   * Flag indicating that the user was warned and still really wants to see this on a mobile view
   */
  public forceMobile: boolean = false;


  /**
   * WRF job definition
   */
  public job: WrfJob = {
    name: 'Bermuda to Jonestown',
    initializationTime: ['2022-05-20 12:00:00', '2022-05-21 00:00:00', '2022-05-21 12:00:00'],
    domainCenter: {
      latitude: 20,
      longitude: -70
    },
    layers: [
      {
        name: 'T2',
        displayName: '2m Temperature',
        palette: {
          name: 'temperature',
          min: -40,
          max: 40
        },
        units: 'ºC',
        visible: true,
        opacity: 1
      },
      {
        name: 'P24M',
        displayName: 'Precipitation (24h)',
        palette: {
          name: 'moisture',
          min: 0,
          max: 300
        },
        units: 'mm',
        visible: false,
        opacity: 1
      }
    ]
};


  /**
   * OpenLayers map
   */
  private map: Map|undefined;


  /**
   * Initialize the layer request
   */
  public req: LayerRequest = {
    height: 950
  };


  /**
   * List of valid height value selections
   */
  public validHeights: number[] = [950, 850, 700, 500, 300, 200];


  /**
   * Get the singleton app object
   */
  constructor()
  {
    WrfViewerComponent.singleton = this;
    this.app = AppComponent.singleton;
  }


  /**
   * Initialize when the view is ready
   */
  ngOnInit(): void
  {
  }


  /**
   * Initialize when the view is ready
   */
  ngAfterViewInit(): void
  {
    this.initMap();
  }


  /**
   * Initialize the map
   * @private
   */
  private initMap(): void
  {
    useGeographic();
    this.map = new Map({
      target: 'map',
      layers: [
        new TileLayer({source: new OSM()}),
      ],
      view: new View({
        center: [
          this.job.domainCenter.longitude,
          this.job.domainCenter.latitude
        ],
        zoom: 5.5
      })
    });

    this.map.on('click', this.mapClicked.bind(this));
  }


  /**
   * Handle a click on the map event
   *
   * @param event
   * @private
   */
  private mapClicked(event: any): void
  {
  }


  public heightChanged(event: MatSliderChange): void
  {
    /* ignore changes with no value */
    if (event.value === null)
      return;

    /* find the closest valid height and set it */
    let closest: number = this.validHeights[0];
    let diff: number = Math.abs(closest - event.value);

    /* check each valid height */
    for (let height of this.validHeights)
    {
      if (diff > Math.abs(height - event.value))
      {
        closest = height;
        diff = Math.abs(closest - event.value);
      }
    }

    /* set the slider value to the closest valid height */
    setTimeout(() => {this.req.height = closest;}, 50);
  }
}
