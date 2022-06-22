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

@NgModule({
  declarations: [
    AppComponent,
    HomeComponent,
    LoginComponent,
    ManageUsersComponent,
    LaunchWrfComponent,
    ViewJobsComponent,
    PreferencesComponent,
    LogoutComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    MatButtonModule,
    MatGridListModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule
{
}
