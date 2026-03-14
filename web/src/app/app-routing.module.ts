import {NgModule} from '@angular/core';
import {Routes, RouterModule} from '@angular/router';
import {HomeComponent} from './home/home';
import {LoginComponent} from './login/login';
import {LogoutComponent} from './logout/logout';
import {LaunchWrfComponent} from './launch-wrf/launch-wrf';
import {ManageUsersComponent} from './manage-users/manage-users';
import {PreferencesComponent} from './preferences/preferences';
import {ViewJobsComponent} from "./view-jobs/view-jobs";
import {WrfViewerComponent} from "./wrf-viewer/wrf-viewer";
import {ActivateComponent} from './activate/activate';
import {ResetPasswordComponent} from './reset-password/reset-password';
import {ModelConfigComponent} from "./model-config/model-config";

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
  {path: 'prefs', component: PreferencesComponent},
  {path: 'activate', component: ActivateComponent},
  {path: 'reset', component: ResetPasswordComponent},
  {path: 'configs', component: ModelConfigComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes, {})],
  exports: [RouterModule]
})
export class AppRoutingModule
{
}
