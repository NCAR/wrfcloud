import {Component, Input, OnInit} from '@angular/core';
import {WrfLayer} from "../client-api";
import {WrfViewerComponent} from "../wrf-viewer/wrf-viewer.component";

@Component({
  selector: 'app-layer',
  templateUrl: './layer.component.html',
  styleUrls: ['./layer.component.sass']
})
export class LayerComponent implements OnInit
{
  @Input() layer: WrfLayer|undefined;


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
}
