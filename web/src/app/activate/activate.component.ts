import {Component, OnInit} from '@angular/core';
import {AppComponent} from "../app.component";
import {ActivateUserRequest, ActivateUserResponse} from "../wrfcloud-api";

@Component({
  selector: 'app-activate',
  templateUrl: './activate.component.html',
  styleUrls: ['./activate.component.sass']
})
export class ActivateComponent implements OnInit
{
  /**
   * App singleton reference
   */
  public app: AppComponent;


  /**
   * API request
   */
  public request: ActivateUserRequest = {
    email: '',
    activation_key: '',
    new_password: ''
  };


  /**
   * Waiting for API flag
   */
  public busy: boolean = false;


  /**
   * API response is successful
   */
  public success: boolean = false;


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
   * Confirm the password was typed correctly
   */
  public confirmPassword: string = '';


  /**
   * Initialize
   */
  constructor()
  {
    /* get app singleton reference */
    this.app = AppComponent.singleton;

    /* parse the request parameters from the query string parameters */
    this.parseQueryStringParameters();
  }


  /**
   * Initialize
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
      if (name === 'email' || name == 'activation_key')
        this.request[name] = decodeURIComponent(value);
    }
  }


  /**
   * Send an activation request to the API
   */
  public sendActivateRequest(): void
  {
    this.app.api.sendActivateUserRequest(this.request, this.handleResponse.bind(this));
  }


  /**
   * Handle a response from the API
   *
   * @param response
   */
  public handleResponse(response: ActivateUserResponse): void
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


  /**
   * Validate the new password and set any errors
   */
  public validate(): void
  {
    this.showMatchError = this.request.new_password !== this.confirmPassword;
    this.showLengthError = this.request.new_password.length > 0 && this.request.new_password.length < 10;
    this.valid = !this.showLengthError && !this.showMatchError;
  }
}
