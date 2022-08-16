import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WrfViewerComponent } from './wrf-viewer.component';

describe('WrfViewerComponent', () => {
  let component: WrfViewerComponent;
  let fixture: ComponentFixture<WrfViewerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ WrfViewerComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WrfViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
