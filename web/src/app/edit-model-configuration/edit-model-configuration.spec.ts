import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EditModelConfigurationComponent } from './edit-model-configuration';

describe('EditModelConfigurationComponent', () => {
  let component: EditModelConfigurationComponent;
  let fixture: ComponentFixture<EditModelConfigurationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ EditModelConfigurationComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(EditModelConfigurationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
