import {NgModule} from '@angular/core';
import {Routes, RouterModule} from '@angular/router';
import {HomeComponent} from "./home/home.component";
import {LoginComponent} from "./login/login.component";
import {LogoutComponent} from "./logout/logout.component";
import {LaunchWrfComponent} from "./launch-wrf/launch-wrf.component";
import {ManageUsersComponent} from "./manage-users/manage-users.component";
import {PreferencesComponent} from "./preferences/preferences.component";
import {ViewJobsComponent} from "./view-jobs/view-jobs.component";
import {WrfViewerComponent} from "./wrf-viewer/wrf-viewer.component";
import {ActivateComponent} from "./activate/activate.component";

const routes: Routes = [
  {path: '', component: HomeComponent},
  {path: 'login', component: LoginComponent},
  {path: 'logout', component: LogoutComponent},
  {path: 'users', component: ManageUsersComponent},
  {path: 'activate', component: ActivateComponent},
  {path: 'launch', component: LaunchWrfComponent},
  {path: 'jobs', component: ViewJobsComponent},
  {path: 'view', component: WrfViewerComponent},
  {path: 'view/:job_id', component: WrfViewerComponent},
  {path: 'prefs', component: PreferencesComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes, {relativeLinkResolution: 'legacy'})],
  exports: [RouterModule]
})
export class AppRoutingModule
{
}
