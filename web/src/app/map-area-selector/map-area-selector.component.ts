import {AfterViewInit, Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges} from '@angular/core';
import {Map, View} from 'ol';
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
import {Fill, Stroke, Style} from "ol/style";
import Feature from "ol/Feature.js";
import proj4 from 'proj4';
import {register} from "ol/proj/proj4";
import {Coordinate} from "ol/coordinate";


@Component({
  selector: 'app-map-area-selector',
  templateUrl: './map-area-selector.component.html',
  styleUrls: ['./map-area-selector.component.sass']
})
export class MapAreaSelectorComponent implements OnInit, AfterViewInit, OnChanges
{
  @Input() namelist: any;
  @Output() gridChange = new EventEmitter<any>();

  private map: Map | undefined;


  /**
   * Map of available projections (display name -> projection value)
   */
  public projections: {[key: string]: string} = {
    'Mercator': 'EPSG:3857',
    'Lambert': 'SR-ORG:29'
  };


  /**
   * Currently selected projection value
   */
  public projection: string = this.projections['Mercator'];


  /**
   * Current map center
   */
  public mapCenter: Array<number> = [0, 0];


  /**
   * Current map zoom level
   */
  public mapZoom: number = 0;


  /**
   * Current domain corner 1
   * @private
   */
  private boxStartCoords: Array<number>|undefined;


  /**
   * Current domain corner 2
   * @private
   */
  private boxEndCoords: Array<number>|undefined;


  /**
   * Current sanitized north bounds of domain
   */
  public north: number = 0;


  /**
   * Current sanitized south bounds of domain
   */
  public south: number = 0;


  /**
   * Current sanitized east bounds of domain
   */
  public east: number = 0;


  /**
   * Current sanitized west bounds of domain
   */
  public west: number = 0;


  /**
   * Current raw grid resolution
   */
  public gridResolution: number = 4000;


  /**
   * Boilerplate GeoJSON to define a polygon
   * @private
   */
  private box: any = {
    'type': 'Feature',
    'geometry': {
      'type': 'Polygon'
    }
  };


  /**
   * Reference to the layer containing the domain boundary polygon
   * @private
   */
  private domainLayer: VectorLayer<any>|undefined;


  /**
   * Set up the custom projections
   */
  constructor()
  {
    /* define WRF Lambert Conformal Conic projection */
    /* Reference: https://spatialreference.org/ref/sr-org/wrf-lambert-conformal-conic/ */
    proj4.defs('SR-ORG:29', '+proj=lcc +lat_1=33 +lat_2=45 +lat_0=40 +lon_0=-97 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs');
    register(proj4);
  }


  /**
   * No-op
   */
  public ngOnInit()
  {
    this.fromNamelist();
  }


  public ngOnChanges(changes: SimpleChanges)
  {
    if (changes['namelist'] !== undefined)
    {
      /* ignore the first change or any non-changes */
      if (changes['namelist'].firstChange || changes['namelist'].currentValue === changes['namelist'].previousValue)
        return;

      this.namelist = changes['namelist'].currentValue;
      this.fromNamelist();
      this.update();
      this.gridChange.emit(this.createNamelistEvent());
    }
  }


  private fromNamelist(): void
  {
    const refLat: number = Number.parseFloat(this.namelist.geogrid.ref_lat.replace(',', '').trim());
    const refLon: number = Number.parseFloat(this.namelist.geogrid.ref_lon.replace(',', '').trim());
    const dx: number = Number.parseFloat(this.namelist.geogrid.dx.replace(',', '').trim());
    const dy: number = Number.parseFloat(this.namelist.geogrid.dy.replace(',', '').trim());
    const nx: number = Number.parseFloat(this.namelist.geogrid.e_we.replace(',', '').trim());
    const ny: number = Number.parseFloat(this.namelist.geogrid.e_sn.replace(',', '').trim());

    const nw: Coordinate = MapAreaSelectorComponent.haversineInverse([refLon, refLat], [-dx * nx / 2, dy * ny / 2]);
    const se: Coordinate = MapAreaSelectorComponent.haversineInverse([refLon, refLat], [dx * nx / 2, -dy * ny / 2]);

    this.north = nw[1];
    this.south = se[1];
    this.west = nw[0];
    this.east = se[0];
    this.gridResolution = dx;

    const mapProj: string = this.namelist.geogrid.map_proj;
    if (mapProj.indexOf('mercator') >= 0)
      this.projection = this.projections['Mercator'];
    else if (mapProj.indexOf('lambert') >= 0)
      this.projection = this.projections['Lambert'];
    else
      this.projection = this.projections['Mercator'];
  }


  private createNamelistEvent(): any
  {
    /* calculate the center lat/lon */
    const refLat: number = (this.north + this.south) / 2;
    const refLon: number = (this.west + 180 + this.east + 180) / 2 - 180;

    const distX: number = MapAreaSelectorComponent.haversine([this.west, refLat], [this.east, refLat]);
    const distY: number = MapAreaSelectorComponent.haversine([refLon, this.south], [refLon, this.north]);

    const nx: number = Math.round(distX / this.gridResolution);
    const ny: number = Math.round(distY / this.gridResolution);

    return {
      'mapProj': this.projection == 'EPSG:3857' ? 'mercator' : 'lambert',
      'refLat': refLat.toFixed(4) + ',',
      'refLon': refLon.toFixed(4) + ',',
      'dx': this.gridResolution + ',',
      'dy': this.gridResolution + ',',
      'e_we': nx + ',',
      'e_sn': ny + ',',
      'time_step': Math.floor(6 * this.gridResolution / 1000)
    };
  }


  /**
   * Initialize the map once the page is loaded
   */
  public ngAfterViewInit(): void
  {
    setTimeout(this.initMap.bind(this), 250);
  }


  /**
   * Initialize the map in the dialog box
   * @private
   */
  private initMap(): void
  {
    /* initialize OpenLayers to use defaults */
    useGeographic();

    /* empty the map element */
    document.getElementById('area-map')!.innerHTML = '';

    /* set up the map */
    const view: View = new View({
      projection: 'EPSG:3857',
      center: this.mapCenter, zoom: this.mapZoom
    });
    const osmLayer: Layer = new TileLayer({source: new OSM()});
    const domainSource: VectorSource = new VectorSource({});
    this.domainLayer = new VectorLayer({source: domainSource, style: this.getStyle});
    this.map = new Map({
      target: 'area-map',
      layers: [osmLayer, this.domainLayer],
      view: view
    });

    /* allow the user to draw a box */
    const dragBoxInteraction: DragBox = new DragBox({condition: platformModifierKeyOnly})
    dragBoxInteraction.on('boxstart', this.doBoxStart.bind(this));
    dragBoxInteraction.on(['boxdrag', 'boxend'], this.doBoxDrag.bind(this));
    this.map.addInteraction(dragBoxInteraction);

    /* draw a box if we have coordinates */
    this.update(false);
  }


  /**
   * Get a static style for the box on the map
   * @private
   */
  private getStyle(): Style
  {
    return new Style({
      'stroke': new Stroke({color: '#444444', width: 3}),
      'fill': new Fill({color: '#cccccc44'}),
    });
  }


  /**
   * The user has started to draw a box, save the coordinate of the first click
   * @param event Contains the coordinate
   * @private
   */
  private doBoxStart(event: any): void
  {
    /* only process DragBoxEvents */
    if (! (event instanceof DragBoxEvent))
      return;

    /* save the coordinate of the first corner */
    this.boxStartCoords = event.coordinate;
  }


  /**
   * The user is dragging the box corner, save as the second corner point
   * @param event
   * @private
   */
  private doBoxDrag(event: any): void
  {
    /* only process DragBoxEvents */
    if (! (event instanceof DragBoxEvent))
      return;

    /* save the coordinate of the second corner */
    this.boxEndCoords = event.coordinate;

    /* draw a new box on the map if user is finished */
    if (event.type === 'boxend')
      this.update();
  }


  /**
   * Flip E-W, N-S if necessary
   * @private
   */
  private sanitizeUserCorners(): void
  {
    if (this.map === undefined || this.domainLayer === undefined || this.boxStartCoords === undefined || this.boxEndCoords === undefined)
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
  }


  /**
   * The user changed the projection type
   * @param event
   */
  public doProjectionChanged(event: any): void
  {
    /* ignore events not from user */
    if (! event.isUserInput)
      return;

    /* store some view parameters from the current view */
    const view: View = this.map!.getView();
    this.mapCenter = view.getCenter()!;
    this.mapZoom = view.getZoom()!;
  }


  /**
   * A value somewhere has changed, so re-compute everything
   *
   * @param emit Should this component emit an event for this update
   */
  public update(emit: boolean = true): void
  {
    /* Sanitize the corners drawn by the user */
    this.sanitizeUserCorners();

    /* Estimate nx,ny from user selected lat/lon corners and dx,dy */
    const dx: number = this.gridResolution;
    const nx: number = 1 + Math.round(MapAreaSelectorComponent.haversine([this.west, this.south], [this.east, this.south]) / dx);
    const ny: number = 1 + Math.round(MapAreaSelectorComponent.haversine([this.east, this.north], [this.east, this.south]) / dx);

    /* Convert new corners back to lat/lon values */
    let sw: Coordinate = [this.west, this.south];
    let se: Coordinate = MapAreaSelectorComponent.haversineInverse(sw, [dx*nx, 0]);
    let ne: Coordinate = MapAreaSelectorComponent.haversineInverse(se, [0, dx*ny]);
    let nw: Coordinate = MapAreaSelectorComponent.haversineInverse(ne, [-dx*nx, 0]);

    /* put simple back in */
    sw = [this.west, this.south];
    se = [this.east, this.south];
    nw = [this.west, this.north];
    ne = [this.east, this.north];

    /* Draw the grid boundary on the map */
    this.drawBox(sw, se, nw, ne);

    /* maybe emit an event */
    if (emit)
      this.gridChange.emit(this.createNamelistEvent());
  }


  /**
   * Draw a box on the map
   *
   * @param sw South-west corner
   * @param se South-east corner
   * @param nw North-west corner
   * @param ne North-east corner
   * @private
   */
  private drawBox(sw: Coordinate, se: Coordinate, nw: Coordinate, ne: Coordinate): void
  {
    /* make sure the map is ready */
    if (this.map === undefined || this.domainLayer === undefined)
      return;

    /* find the vector layer and add a polygon representing the domain boundaries */
    this.box['geometry']['coordinates'] = [[ nw, ne, se, sw, nw ]];
    const source: VectorSource = new VectorSource({
        features: new GeoJSON().readFeatures(this.box)
    });
    this.domainLayer.setSource(source);
    this.domainLayer.setVisible(true);
    this.domainLayer.changed();
    this.map.render();
  }


  /**
   * Compute the distance in meters between two lon/lat points
   *
   * @param pt1
   * @param pt2
   * @return Distance in meters between the two points
   * @private
   */
  private static haversine(pt1: Coordinate, pt2: Coordinate): number
  {
    const lon1: number = Math.PI * pt1[0] / 180;
    const lat1: number = Math.PI * pt1[1] / 180;
    const lon2: number = Math.PI * pt2[0] / 180;
    const lat2: number = Math.PI * pt2[1] / 180;

    const dlon: number = lon2 - lon1;
    const dlat: number = lat2 - lat1;
    const a: number = Math.pow(Math.sin(dlat / 2), 2) + Math.cos(lat1) * Math.cos(lat2) * Math.pow(Math.sin(dlon / 2), 2);
    const c: number = 2 * Math.asin(Math.sqrt(a));
    const R: number = 6366707.01953610771;  // mean radius of the earth
    const m: number = R * c;

    return  m;
  }


  /**
   * Compute the lon/lat point a given distance from another point
   *
   * @param pt1 Initial lon/lat point
   * @param dist Distances in kilometers [dx, dy] dx:+=north/-=south, dy:+=east/-=west
   * @return Distance in meters between the two points
   * @private
   */
  private static haversineInverse(pt1: Coordinate, dist: Coordinate): Coordinate
  {
    const lon1: number = pt1[0];
    const lat1: number = pt1[1];

    const dx: number = dist[0];
    const dy: number = dist[1];

    const lat2: number = lat1 + (dy / 111120);
    const lon2: number = lon1 + (dx / (111120 * Math.abs(Math.cos(lat2 * Math.PI/180))));

    return [lon2, lat2];
  }
}
