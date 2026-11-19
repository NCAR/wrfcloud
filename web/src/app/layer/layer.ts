import {Component, Input, OnInit} from '@angular/core';
import {WrfLayerGroup} from "../client-api";
import {WrfViewerComponent} from "../wrf-viewer/wrf-viewer";
import {legendGradient, legendMax, legendTicks, LegendTick} from "./legend-gradient";
import {Palette} from '@ncar/colors';


@Component({
    selector: 'app-layer',
    templateUrl: './layer.html',
    styleUrls: ['./layer.sass'],
    standalone: false
})
export class LayerComponent implements OnInit
{
  @Input() layerGroup: WrfLayerGroup|undefined;

  /**
   * 'controls' shows the visibility checkbox and opacity slider (side panel),
   * 'legend' shows only the color legend (under the map)
   */
  @Input() mode: 'controls'|'legend' = 'controls';


  /**
   * Viewer singleton to manipulate layers on the map
   */
  private viewer: WrfViewerComponent;

  /**
   * Palette that the cached legend ticks were made for
   */
  private ticksPalette: any = undefined;


  /**
   * Cached legend ticks
   */
  private ticksCache: LegendTick[] = [];


  constructor()
  {
    this.viewer = WrfViewerComponent.singleton;
  }


  ngOnInit(): void
  {
  }


  /**
   * Get the CSS background for the color legend, or null to fall back on the palette-<name> CSS class
   */
  public legendBackground(): string|null
  {
    return this.layerGroup ? new Palette(this.layerGroup.palette.palette_name).getLinearGradient() : null;
  }


  /**
   * Get the value to label the high end of the color legend with
   */
  public legendMaxValue(): number|undefined
  {
    return this.layerGroup ? legendMax(this.layerGroup.palette) : undefined;
  }


  /**
   * Get the labeled ticks for the color legend, or an empty list to label only the min and max.  The list is cached for each palette
   * so the template does not get a new list on every change detection pass.
   */
  public legendTickList(): LegendTick[]
  {
    const palette = this.layerGroup?.palette;
    if (palette === undefined)
      return [];
    if (palette !== this.ticksPalette)
    {
      this.ticksPalette = palette;
      this.ticksCache = legendTicks(palette);
    }
    return this.ticksCache;
  }


  public percentLabel(value: number): string
  {
    return Math.round(value * 100) + '%';
  }
}
