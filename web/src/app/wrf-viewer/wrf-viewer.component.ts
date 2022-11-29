import {Component, OnInit} from '@angular/core';
import {AppComponent} from "../app.component";
import {
  WrfJob,
  LayerRequest,
  GetWrfGeoJsonRequest,
  GetWrfGeoJsonResponse,
  ListJobRequest, ListJobResponse, WrfLayerGroup, WrfLayer
} from "../client-api";
import {Map, View} from 'ol';
import TileLayer from 'ol/layer/Tile';
import {OSM} from 'ol/source';
import {MatSliderChange} from "@angular/material/slider";
import {useGeographic} from "ol/proj";
import VectorSource from "ol/source/Vector";
import {GeoJSON} from "ol/format";
import VectorLayer from "ol/layer/Vector";
import {Fill, Stroke, Style} from "ol/style";
import {Layer} from "ol/layer";
import LayerGroup from "ol/layer/Group";

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
  public selectedFrameMs: number = 0;


  /**
   * WRF job definition
   */
  public job: WrfJob|undefined;


  /**
   * A list of layers taken from the job
   */
  public layers: WrfLayer[] = [];


  /**
   * Layer groups organized by variable name
   */
  public layerGroups: WrfLayerGroup[] = [];


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
   * A map to store data frames, which are OL6 GeoJSON Layers
   */
  public frames: {[key: string]: Layer} = {};


  /**
   * Get the singleton app object
   */
  constructor()
  {
    WrfViewerComponent.singleton = this;
    this.app = AppComponent.singleton;

    /* request the job information */
    this.sendGetJobRequest();
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
    /* wait for the job to be defined */
    if (this.job === undefined)
    {
      setTimeout(this.initMap.bind(this), 100);
      return;
    }

    useGeographic();
    this.map = new Map({
      target: 'map',
      layers: [
        new TileLayer({source: new OSM()}),
      ],
      view: new View({
        center: [
          this.job.domain_center.longitude,
          this.job.domain_center.latitude
        ],
        zoom: 5.5
      })
    });

    this.map.on('click', this.mapClicked.bind(this));
  }


  /**
   *
   * @param jobId
   * @param validTime
   * @param variable
   * @private
   */
  private loadLayer(jobId: string, validTime: number, variable: string): void
  {
    /* create the request data */
    const requestData: GetWrfGeoJsonRequest = {
      job_id: jobId,
      valid_time: validTime,
      variable: variable
    };

    this.app.api.sendGetWrfGeoJsonRequest(requestData, this.handleGetWrfGeoJsonResponse.bind(this));
  }


  /**
   *
   * @param response
   * @private
   */
  private handleGetWrfGeoJsonResponse(response: GetWrfGeoJsonResponse): void
  {
    /* handle an error case */
    if (!response.ok)
    {
      this.app.showErrorDialog(response.errors);
      return;
    }

    /* find the metadata layer */
    let layerIndex = 0;
    while (layerIndex < this.layers.length)
    {
      if (response.data.variable === this.layers[layerIndex].variable_name)
        if (response.data.valid_time === this.layers[layerIndex].dt)
          if (response.data.z_level === this.layers[layerIndex].z_level)
            break;
      layerIndex++;
    }
    const layer: WrfLayer|undefined = (layerIndex < this.layers.length) ? this.layers[layerIndex] : undefined;

    /* decode the base64 data */
    const geojsonObject = JSON.parse(atob(response.data.geojson));
    if (layer)
      layer.layer_data = geojsonObject;

    /* create a new layer for the map */
    const vectorSource = new VectorSource({features: new GeoJSON().readFeatures(geojsonObject)});
    const vectorLayer = new VectorLayer({source: vectorSource, style: WrfViewerComponent.selfStyle});
    if (layer) vectorLayer.setOpacity(layer.opacity);

    /* cache the layer in the frames map */
    const frameKey = WrfViewerComponent.generateFrameKey(response.data);
    this.frames[frameKey] = vectorLayer;

    /* add the invisible layer to the map */
    vectorLayer.setVisible(false);
    this.map!.addLayer(vectorLayer);

    /* advance the loading progress */
    let layerGroup: WrfLayerGroup = this.layerGroups[0];
    for (let lg of this.layerGroups)
    {
      const varMatch: boolean = response.data.variable === lg.variable_name;
      const zMatch: boolean = response.data.z_level === lg.z_level || lg.z_level === null || lg.z_level === undefined;
      if (varMatch && zMatch)
        lg.loaded += 1;
    }

    /* load the first frame if finished loading */
    if (layerGroup.loaded === layerGroup.layers.length)
    {
      const key = WrfViewerComponent.generateFrameKey({
        'job_id': response.data.job_id,
        'valid_time': this.selectedFrameMs / 1000,
        'variable': response.data.variable
      });
      this.frames[key].setVisible(true);
    }
  }


  /**
   * Send a request to get selected job details
   * @private
   */
  private sendGetJobRequest(): void
  {
    /* get the job ID from the URI */
    const jobId: string = this.app.router.url.split('/')[2];

    /* send an API request to get the job details */
    const req: ListJobRequest = {job_id: jobId};
    this.app.api.sendListJobsRequest(req, this.handleGetJobResponse.bind(this));
  }


  /**
   * Receive the job details
   *
   * @param response
   * @private
   */
  private handleGetJobResponse(response: ListJobResponse): void
  {
    /* check for status and errors */
    if (!response.ok)
    {
      this.app.showErrorDialog(response.errors);
      return;
    }

    /* extract the WRF job data from the response */
    this.job = response.data.jobs[0];

    /* extract the layers from the job data */
    this.layers = this.job.layers;
    this.layerGroups = [];
    const tmpMap: {[key: string]: WrfLayerGroup} = {};
    for (let layer of this.job.layers)
    {
      let group: WrfLayerGroup = tmpMap[layer.variable_name];
      if (group === undefined)
      {
        group = {
          layers: [],
          loaded: 0,
          opacity: layer.opacity,
          variable_name: layer.variable_name,
          visible: layer.visible,
          z_level: layer.z_level,
          display_name: layer.display_name,
          opacityChange: this.doChangeOpacity.bind(this),
          visibilityChange: this.doToggleLayer.bind(this)
        };
        tmpMap[layer.variable_name] = group;
        this.layerGroups[this.layerGroups.length] = group;
      }
      group.layers[group.layers.length] = layer;
    }

    /* set up the animation frame list */
    for (let layer of this.layerGroups[0].layers)
      this.animationFrames[this.animationFrames.length] = new Date(layer.dt * 1000);
    this.animationFrames = this.animationFrames.sort();
    this.selectedFrameMs = this.animationFrames[0].getTime();
  }


  /**
   * Generate a string to identify a particular frame, which is an OpenLayers Layer
   * @param data
   * @private
   */
  private static generateFrameKey(data: {[key: string]: string|number}): string
  {
    return data['job_id'] + '-' + data['valid_time'] + '-' + data['variable'];
  }


  /**
   * Use the styling that is already in the feature -- don't know why OpenLayers can't do this
   * @param feature
   * @private
   */
  private static selfStyle(feature: any): Style
  {
    return new Style({
      fill: new Fill({color: feature.getProperties().fill})
    });
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
   * Toggle a data layer on/off
   * @param layer
   */
  public doToggleLayer(layer: WrfLayerGroup): void
  {
    if (layer.visible)
      this.preloadFrames(this.job!.job_id, layer.variable_name);
  }


  public doChangeOpacity(layer: WrfLayerGroup): void
  {
    for (let key of Object.keys(this.frames))
    {
      const frame: Layer = this.frames[key];
      frame.setOpacity(layer.opacity);
    }
  }

  /**
   * Start the process of preloading data frames
   *
   * @param jobId
   * @param variable
   */
  public preloadFrames(jobId: string, variable: string): void
  {
    /* load a data layer if it is not yet loaded */
    for (let validTime of this.animationFrames)
    {
      const timestamp: number = Math.trunc(validTime.getTime() / 1000);
      const frameKey = WrfViewerComponent.generateFrameKey(
        {
          'job_id': jobId,
          'valid_time': timestamp,
          'variable': variable
        }
      );
      if (this.frames[frameKey] === undefined)
        this.loadLayer(jobId, timestamp, variable);
    }
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
    let variableName: string = '';
    for (let lg of this.layerGroups)
      if (lg.visible)
        variableName = lg.variable_name;

    /* hide the layer that corresponds to the current time */
    let frameKey = WrfViewerComponent.generateFrameKey(
      {'job_id': this.job!.job_id,
        'valid_time': Math.trunc(this.selectedFrameMs / 1000),
        'variable': variableName
      }
    );
    if (this.frames[frameKey] !== undefined)
      this.frames[frameKey].setVisible(false);

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

    /* adjust the frame index to be within array index bounds -- loop the animation if we go passed the end (or beginning) */
    while (selectedIndex < 0)
      selectedIndex += this.animationFrames.length;
    while (selectedIndex >= this.animationFrames.length)
      selectedIndex -= this.animationFrames.length;

    /* update the selected frame */
    this.selectedFrameMs = this.animationFrames[selectedIndex].getTime();

    /* show the layer that corresponds to the new time */
    frameKey = WrfViewerComponent.generateFrameKey(
      {
        'job_id': this.job!.job_id,
        'valid_time': Math.trunc(this.selectedFrameMs / 1000),
        'variable': variableName
      }
    );
    if (this.frames[frameKey] !== undefined)
      this.frames[frameKey].setVisible(true);
  }
}
