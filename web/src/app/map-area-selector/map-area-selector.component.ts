import {AfterViewInit, Component, Input, OnInit} from '@angular/core';
import {Collection, Map, View} from 'ol';
import {Layer} from 'ol/layer';
import TileLayer from 'ol/layer/Tile';
import {OSM} from 'ol/source';
import {useGeographic} from 'ol/proj';
import {platformModifierKeyOnly} from "ol/events/condition";
import {DragBox} from "ol/interaction";
import {DragBoxEvent} from "ol/interaction/DragBox";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import {GeoJSON} from "ol/format";
import BaseLayer from "ol/layer/Base";
import {Fill, Stroke, Style} from "ol/style";
import Feature from "ol/Feature.js";
import proj4 from 'proj4';
import {register} from "ol/proj/proj4";


@Component({
  selector: 'app-map-area-selector',
  templateUrl: './map-area-selector.component.html',
  styleUrls: ['./map-area-selector.component.sass']
})
export class MapAreaSelectorComponent implements OnInit, AfterViewInit
{
  @Input() namelist: string = '';


  private map: Map | undefined;


  public projections: {[key: string]: string} = {
    'Mercator': 'EPSG:3857',
    'Lambert': 'SR-ORG:29'
  };


  public projection: string = this.projections['Mercator'];


  public mapCenter: Array<number> = [0, 0];


  public mapZoom: number = 0;


  private boxStartCoords: Array<number>|undefined;


  private boxEndCoords: Array<number>|undefined;


  public north: number = 0;
  public south: number = 0;
  public east: number = 0;
  public west: number = 0;
  public gridResolution: number = 4000;


  private box: any = {
    'type': 'Feature',
    'geometry': {
      'type': 'Polygon'
    }
  };

  constructor()
  {
    /* define WRF Lambert Conformal Conic projection */
    /* Reference: https://spatialreference.org/ref/sr-org/wrf-lambert-conformal-conic/ */
    proj4.defs('SR-ORG:29', '+proj=lcc +lat_1=33 +lat_2=45 +lat_0=40 +lon_0=-97 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs');
    register(proj4);
  }

  public ngOnInit()
  {
  }


  public ngAfterViewInit(): void
  {
    this.initMap();
  }


  private initMap(): void
  {
    useGeographic();

    /* empty the map element */
    document.getElementById('area-map')!.innerHTML = '';

    /* set up the map */
    const view: View = new View({
      projection: this.projection,
      center: this.mapCenter, zoom: this.mapZoom
    });
    const osmLayer: Layer = new TileLayer({source: new OSM()});
    const vecSource: VectorSource = new VectorSource({});
    const vecLayer: Layer = new VectorLayer({source: vecSource, style: this.getStyle});
    this.map = new Map({
      target: 'area-map',
      layers: [osmLayer, vecLayer],
      view: view
    });

    /* allow the user to draw a box */
    const dragBoxInteraction: DragBox = new DragBox({condition: platformModifierKeyOnly})
    dragBoxInteraction.on('boxstart', this.doBoxStart.bind(this));
    dragBoxInteraction.on(['boxdrag', 'boxend'], this.doBoxEnd.bind(this));
    this.map.addInteraction(dragBoxInteraction);

    /* draw a box if we have coordinates */
    this.drawBox();
  }


  private getStyle(): Style
  {
    return new Style({
      'stroke': new Stroke({color: '#444444', width: 3}),
      'fill': new Fill({color: '#cccccc44'}),
    });
  }
  private doBoxStart(event: any): void
  {
    if (! (event instanceof DragBoxEvent))
      return;

    this.boxStartCoords = event.coordinate;
  }

  private doBoxEnd(event: any): void
  {
    if (! (event instanceof DragBoxEvent))
      return;

    this.boxEndCoords = event.coordinate;

    this.drawBox();
  }


  private drawBox(): void
  {
    if (this.map === undefined || this.boxStartCoords === undefined || this.boxEndCoords === undefined)
      return;

    /* maybe swap the north/south and east/west values */
    this.north = Math.max(this.boxStartCoords![1], this.boxEndCoords![1]);
    this.south = Math.min(this.boxStartCoords![1], this.boxEndCoords![1]);
    this.east = Math.max(this.boxStartCoords![0], this.boxEndCoords![0]);
    this.west = Math.min(this.boxStartCoords![0], this.boxEndCoords![0]);

    /* adjust values to stay between -180 to 180 and -90 to 90 for longitudes and latitudes respectively */
    while (this.east > 180) this.east -= 360;
    while (this.east < -180) this.east += 360;
    while (this.west > 180) this.west -= 360;
    while (this.west < -180) this.west += 360;

    /* round precision to 4 decimal places, which is on the order of a few meters */
    this.north = Number.parseFloat(this.north.toFixed(4));
    this.south = Number.parseFloat(this.south.toFixed(4));
    this.east = Number.parseFloat(this.east.toFixed(4));
    this.west = Number.parseFloat(this.west.toFixed(4));

    /* find the vector layer and add a polygon representing the domain boundaries */
    const layers: Collection<BaseLayer> = this.map.getLayers();
    for (let i = 0; i < layers.getLength(); i++)
    {
      const layer: BaseLayer = layers.item(i);
      if (layer instanceof VectorLayer)
      {
        this.box['geometry']['coordinates'] = [[
          [this.west, this.north],
          [this.east, this.north],
          [this.east, this.south],
          [this.west, this.south],
          [this.west, this.north]
        ]];
        const source: VectorSource = new VectorSource({
            features: new GeoJSON().readFeatures(this.box)
        });
        layer.setSource(source);
        layer.setVisible(true);
        layer.changed();
        this.map.render();
      }
    }
  }


  public updateBox(): void
  {
    this.boxStartCoords = [this.east, this.north];
    this.boxEndCoords = [this.west, this.south];

    this.drawBox();
  }


  public doProjectionChanged(event: any): void
  {
    /* ignore events not from user */
    if (! event.isUserInput)
      return;

    /* store some view parameters from the current view */
    const view: View = this.map!.getView();
    this.mapCenter = view.getCenter()!;
    this.mapZoom = view.getZoom()!;

    /* get a new map */
    setTimeout(this.initMap.bind(this), 250);
  }
}
