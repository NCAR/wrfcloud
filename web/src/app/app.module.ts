import {NgModule} from '@angular/core';
import {BrowserModule} from '@angular/platform-browser';

import {AppRoutingModule} from './app-routing.module';
import {AppComponent} from './app.component';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {MatMenuModule} from "@angular/material/menu";
import {MatIconModule} from "@angular/material/icon";
import {MatInputModule} from "@angular/material/input";
import {FormsModule} from "@angular/forms";
import {MatRippleModule} from "@angular/material/core";
import {HttpClientModule} from "@angular/common/http";
import {MatExpansionModule} from "@angular/material/expansion";
import {MatDialogModule} from "@angular/material/dialog";
import {MatDividerModule} from "@angular/material/divider";
import {MatTableModule} from "@angular/material/table";
import {MatPaginatorModule} from "@angular/material/paginator";
import {MatSortModule} from "@angular/material/sort";
import {MatSelectModule} from "@angular/material/select";
import {MatSliderModule} from "@angular/material/slider";
import {MatProgressBarModule} from "@angular/material/progress-bar";
import {MatCheckboxModule} from "@angular/material/checkbox";

import {HomeComponent} from './home/home.component';
import {LoginComponent} from './login/login.component';
import {MatButtonModule} from "@angular/material/button";
import {MatGridListModule} from "@angular/material/grid-list";
import {ManageUsersComponent} from './manage-users/manage-users.component';
import {LaunchWrfComponent} from './launch-wrf/launch-wrf.component';
import {ViewJobsComponent} from './view-jobs/view-jobs.component';
import {ErrorDialogComponent} from './error-dialog/error-dialog.component';
import {EditUserComponent} from './edit-user/edit-user.component';
import {WrfViewerComponent} from './wrf-viewer/wrf-viewer.component';
import {ActivateComponent} from "./activate/activate.component";
import {ResetPasswordComponent} from './reset-password/reset-password.component';
import {LayerComponent} from './layer/layer.component';
import {PreferencesComponent} from './preferences/preferences.component';
import {LogoutComponent} from './logout/logout.component';
import {MatBadgeModule} from "@angular/material/badge";
import {MatDatepickerModule} from "@angular/material/datepicker";
import {MatNativeDateModule} from "@angular/material/core";


@NgModule({
  declarations: [
    ActivateComponent,
    AppComponent,
    EditUserComponent,
    ErrorDialogComponent,
    HomeComponent,
    LaunchWrfComponent,
    LayerComponent,
    LoginComponent,
    LogoutComponent,
    ManageUsersComponent,
    PreferencesComponent,
    ViewJobsComponent,
    WrfViewerComponent,
    ResetPasswordComponent
  ],
    imports: [
        BrowserModule,
        AppRoutingModule,
        HttpClientModule,
        BrowserAnimationsModule,
        MatButtonModule,
        MatGridListModule,
        MatMenuModule,
        MatIconModule,
        MatInputModule,
        FormsModule,
        MatRippleModule,
        MatExpansionModule,
        MatDialogModule,
        MatDividerModule,
        MatTableModule,
        MatPaginatorModule,
        MatSortModule,
        MatSelectModule,
        MatProgressBarModule,
        MatSliderModule,
        MatCheckboxModule,
        MatBadgeModule,
        MatDatepickerModule,
        MatNativeDateModule
    ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule
{
}
