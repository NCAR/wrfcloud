import {NgModule} from '@angular/core';
import {BrowserModule} from '@angular/platform-browser';

import {AppRoutingModule} from './app-routing.module';
import {AppComponent} from './app.component';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {HomeComponent} from './home/home.component';
import {LoginComponent} from './login/login.component';
import {MatButtonModule} from "@angular/material/button";
import {MatGridListModule} from "@angular/material/grid-list";
import {ManageUsersComponent} from './manage-users/manage-users.component';
import {LaunchWrfComponent} from './launch-wrf/launch-wrf.component';
import {ViewJobsComponent} from './view-jobs/view-jobs.component';
import {PreferencesComponent} from './preferences/preferences.component';
import {LogoutComponent} from './logout/logout.component';
import {MatMenuModule} from "@angular/material/menu";
import {MatIconModule} from "@angular/material/icon";
import {MatInputModule} from "@angular/material/input";
import {FormsModule} from "@angular/forms";
import {MatRippleModule} from "@angular/material/core";
import {HttpClientModule} from "@angular/common/http";
import {MatExpansionModule} from "@angular/material/expansion";
import {MatDialogModule} from "@angular/material/dialog";
import {ErrorDialogComponent} from './error-dialog/error-dialog.component';
import {MatDividerModule} from "@angular/material/divider";
import {MatTableModule} from "@angular/material/table";
import {MatPaginatorModule} from "@angular/material/paginator";
import {MatSortModule} from "@angular/material/sort";
import {EditUserComponent} from './edit-user/edit-user.component';
import {MatSelectModule} from "@angular/material/select";
import {WrfViewerComponent} from './wrf-viewer/wrf-viewer.component';
import {ActivateComponent} from "./activate/activate.component";
import {MatSliderModule} from "@angular/material/slider";

@NgModule({
  declarations: [
    AppComponent,
    HomeComponent,
    LoginComponent,
    ManageUsersComponent,
    LaunchWrfComponent,
    ViewJobsComponent,
    PreferencesComponent,
    LogoutComponent,
    ErrorDialogComponent,
    EditUserComponent,
    ActivateComponent,
    WrfViewerComponent
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
    MatSliderModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule
{
}
