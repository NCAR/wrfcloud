import {NgModule} from '@angular/core';
import {Routes, RouterModule} from '@angular/router';
import {HomeComponent} from "./home/home.component";
import {LoginComponent} from "./login/login.component";
import {LogoutComponent} from "./logout/logout.component";
import {LaunchWrfComponent} from "./launch-wrf/launch-wrf.component";
import {ManageUsersComponent} from "./manage-users/manage-users.component";
import {PreferencesComponent} from "./preferences/preferences.component";
import {ViewJobsComponent} from "./view-jobs/view-jobs.component";

const routes: Routes = [
  {path: '', component: HomeComponent},
  {path: 'login', component: LoginComponent},
  {path: 'logout', component: LogoutComponent},
  {path: 'users', component: ManageUsersComponent},
  {path: 'launch', component: LaunchWrfComponent},
  {path: 'jobs', component: ViewJobsComponent},
  {path: 'prefs', component: PreferencesComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes, {relativeLinkResolution: 'legacy'})],
  exports: [RouterModule]
})
export class AppRoutingModule
{
}
