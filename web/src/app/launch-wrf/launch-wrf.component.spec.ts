import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LaunchWrfComponent } from './launch-wrf.component';

describe('LaunchWrfComponent', () => {
  let component: LaunchWrfComponent;
  let fixture: ComponentFixture<LaunchWrfComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ LaunchWrfComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LaunchWrfComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
