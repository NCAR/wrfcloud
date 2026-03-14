import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ViewJobsComponent } from './view-jobs';

describe('ViewJobsComponent', () => {
  let component: ViewJobsComponent;
  let fixture: ComponentFixture<ViewJobsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ViewJobsComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ViewJobsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
