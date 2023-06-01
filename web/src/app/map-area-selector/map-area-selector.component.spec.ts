import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MapAreaSelectorComponent } from './map-area-selector.component';

describe('MapAreaSelectorComponent', () => {
  let component: MapAreaSelectorComponent;
  let fixture: ComponentFixture<MapAreaSelectorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ MapAreaSelectorComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MapAreaSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
