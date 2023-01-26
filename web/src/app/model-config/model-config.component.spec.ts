import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ModelConfigComponent } from './model-config.component';

describe('ModelConfigComponent', () => {
  let component: ModelConfigComponent;
  let fixture: ComponentFixture<ModelConfigComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ModelConfigComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ModelConfigComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
