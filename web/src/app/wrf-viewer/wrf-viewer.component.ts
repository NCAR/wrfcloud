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
   * List of visible animation controls
   */
  public animationControls: string[] = ['back', 'play', 'forward'];


  /**
   * Flag to tell us if we are animating
   */
  public playing: boolean = false;


  /**
   * Delay in milliseconds between
   */
  public animationDelayMs: number = 100;


  /**
   * List of animation frames
   */
  public animationFrames: Date[] = [];


  /**
   * The selected animation frame
   */
  public selectedFrameMs: number;


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

    /* TODO: Get frame list from API */
    for (let t = new Date(2022, 4, 20, 12, 0, 0, 0).getTime(); t < new Date(2022, 4, 21, 12, 0, 0, 0).getTime(); t += 1200000)
      this.animationFrames.push(new Date(t));
    this.selectedFrameMs = this.animationFrames[0].getTime();
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


  /**
   * Handle animate action
   */
  public doAnimate(event: any, action: string): void
  {
    if (action === 'play')
    {
      this.doTogglePlay();
      this.doPlayAnimation();
    }
    else if (action === 'pause')
    {
      this.doTogglePlay();
      this.doPauseAnimation();
    }
    else if (action === 'back')
    {
      this.doStepAnimation(-1);
    }
    else if (action === 'forward')
    {
      this.doStepAnimation(1);
    }
  }


  /**
   * Updated the 'selectedFrame' value to be the nearest available frame
   */
  public doSelectNearestFrame(): void
  {
    /* skip if there are no animation frames loaded */
    if (this.animationFrames.length === 0)
      return;

    /* if there is no frame selected, then select one */

    /* initialize values */
    let nearest: Date = this.animationFrames[0];
    let diff: number = Number.MAX_VALUE;

    /* loop over all animation frames */
    for (let frame of this.animationFrames)
    {
      /* calculate the difference between the selected frame and this frame */
      const thisDiff = Math.abs(frame.getTime() - this.selectedFrameMs);

      /* maybe update the nearest frame */
      if (thisDiff < diff)
      {
        nearest = frame;
        diff = thisDiff;
      }
    }

    /* update the selected frame to be the nearest frame */
    this.selectedFrameMs = nearest.getTime();
  }


  public doTogglePlay(): void
  {
    this.animationControls[1] = this.animationControls[1] === 'play' ? 'pause' : 'play';
  }


  private doPlayAnimation()
  {
    this.playing = true;
    this.runAnimation();
  }


  private doPauseAnimation()
  {
    this.playing = false;
  }


  /**
   * Run the animation
   * @private
   */
  private runAnimation(): void
  {
    if (this.playing)
    {
      this.doStepAnimation();
      setTimeout(this.runAnimation.bind(this), this.animationDelayMs);
    }
  }


  /**
   * Advance the time selected by the given number of steps
   *
   * @param stepSize Number of steps by which to advance the current frame
   * @private
   */
  private doStepAnimation(stepSize: number = 1)
  {
    /* find the currently selected frame's index */
    let selectedIndex: number = 0;
    for (let i = 0; i < this.animationFrames.length; i++)
      if (this.selectedFrameMs === this.animationFrames[i].getTime())
      {
        selectedIndex = i;
        break;
      }

    /* calculate the new index */
    selectedIndex += stepSize;

    /* adjust the frame index to be within array index bounds */
    while (selectedIndex < 0)
      selectedIndex += this.animationFrames.length;
    while (selectedIndex >= this.animationFrames.length)
      selectedIndex -= this.animationFrames.length;

    /* update the selected frame */
    this.selectedFrameMs = this.animationFrames[selectedIndex].getTime();
  }
}
