import {Component, OnInit} from '@angular/core';
import {ResetPasswordRequest, ResetPasswordResponse} from "../client-api";
import {AppComponent} from "../app.component";

@Component({
  selector: 'app-reset-password',
  templateUrl: './reset-password.component.html',
  styleUrls: ['./reset-password.component.sass']
})
export class ResetPasswordComponent implements OnInit
{
  /**
   * Reference to the app singleton
   */
  public app: AppComponent = AppComponent.singleton;


  /**
   * Show an error for the password length
   */
  public showLengthError: boolean = false;


  /**
   * Show an error for the password match
   */
  public showMatchError: boolean = false;


  /**
   * All data entered is valid
   */
  public valid: boolean = false;


  /**
   * Reset API request was successful
   */
  public success: boolean = false;


  /**
   * Reset password request
   */
  request: ResetPasswordRequest = {
    email: '',
    reset_token: '',
    new_password: ''
  };


  /**
   * Field to hold the confirmed password field
   */
  public confirmPassword: string = '';


  /**
   * Flag to lock the UI pending API response
   */
  public busy: boolean = false;


  /**
   * Default constructor
   */
  constructor()
  {
    this.parseQueryStringParameters();
    this.validate();
  }


  /**
   * On init
   */
  ngOnInit(): void
  {
  }


  /**
   * Parse QSP values into the API request
   */
  public parseQueryStringParameters(): void
  {
    /* get the full QSP string without the route */
    const qsp = this.app.router.url.split('?')[1];

    /* get each name/value pair */
    const pairs = qsp.split('&');

    /* split each name/value pair and set the value on the request */
    for (let pair of pairs)
    {
      const tokens = pair.split('=');
      const name = tokens[0];
      const value = tokens[1];
      if (name === 'email' || name == 'reset_token')
        this.request[name] = decodeURIComponent(value);
    }
  }


  /**
   * Validate the new password and set any errors
   */
  public validate(): void
  {
    this.showMatchError = this.request.new_password !== this.confirmPassword;
    this.showLengthError = this.request.new_password.length > 0 && this.request.new_password.length < 10;
    this.valid = !this.showLengthError && !this.showMatchError;
  }


  /**
   * Partially validate the request and send it
   */
  public doReset(): void
  {
    /* validate again */
    if (this.request.new_password.length <= 0)
    {
      this.showLengthError = true;
      this.valid = false;
      return;
    }

    /* send the reset request to the API */
    this.app.api.sendResetPasswordRequest(this.request, this.handleResetPasswordResponse.bind(this));
  }


  /**
   * Handle the reset password API response
   *
   * @param response API response
   */
  public handleResetPasswordResponse(response: ResetPasswordResponse): void
  {
    if (response.ok)
    {
      this.success = true;
      setTimeout(this.app.routeTo.bind(this.app), 2500, 'login');
    }
    else
    {
      this.app.showErrorDialog(response.errors);
    }
  }
}
