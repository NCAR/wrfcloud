import {Component, Input, OnInit} from '@angular/core';
import {WrfLayerGroup} from "../client-api";
import {WrfViewerComponent} from "../wrf-viewer/wrf-viewer";

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
   * Viewer singleton to manipulate layers on the map
   */
  private viewer: WrfViewerComponent;


  constructor()
  {
    this.viewer = WrfViewerComponent.singleton;
  }


  ngOnInit(): void
  {
  }


  public percentLabel(value: number): string
  {
    return Math.round(value * 100) + '%';
  }
}
