import {Component, OnInit} from '@angular/core';
import {AppComponent} from "../app.component";
import {ChangePasswordRequest, ChangePasswordResponse} from "../client-api";

@Component({
  selector: 'app-preferences',
  templateUrl: './preferences.component.html',
  styleUrls: ['./preferences.component.sass']
})
export class PreferencesComponent implements OnInit
{
  /**
   * Reference to the application singleton
   */
  public app: AppComponent;


  /**
   * Waiting for API response
   */
  public busy: boolean = false;


  /**
   * Let us know if the password change was successful
   */
  public passwordChanged: boolean = false;


  /**
   * Change password request
   */
  public chpassReq: ChangePasswordRequest = {
    password0: '',
    password1: '',
    password2: ''
  };


  /**
   * Change password response
   */
  public chpassRes: ChangePasswordResponse = {
    ok: false
  };


  /**
   * Get a reference to the application singleton
   */
  constructor()
  {
    this.app = AppComponent.singleton;

    /* make sure we have user data */
    if (this.app.user === undefined)
      this.app.refreshUserData();
  }


  /**
   *
   */
  ngOnInit(): void
  {
  }


  /**
   * Submit the change password request to the API
   */
  public doChangePassword(): void
  {
    /* start the spinner */
    this.busy = true;

    /* send the request */
    this.app.api.sendChangePasswordRequest(this.chpassReq, this.handleChangePasswordResponse.bind(this));
  }


  /**
   * Handle the change password response message from the API
   */
  public handleChangePasswordResponse(response: ChangePasswordResponse): void
  {
    /* stop the spinner */
    this.busy = false;

    if (response.ok)
    {
      /* show successful results */
      this.passwordChanged = true;
      this.chpassReq.password0 = '';
      this.chpassReq.password1 = '';
      this.chpassReq.password2 = '';
      setTimeout(() => {this.passwordChanged = false;}, 7000);
    }
    else
    {
      this.app.showErrorDialog(response.errors);
    }
  }
}
