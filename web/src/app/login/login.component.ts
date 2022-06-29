import {Component, OnInit} from '@angular/core';
import {AppComponent} from "../app.component";
import {LoginResponse} from "../wrfcloud-api";

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.sass']
})
export class LoginComponent implements OnInit
{
  public app: AppComponent;


  /**
   * Initialize an empty login request
   */
  req: LoginRequest = {email: '', password: ''};


  /**
   * Flag to switch displays to the i-forgot-my-password mode
   */
  iForgot: boolean = false;


  /**
   * Flag that tells the display components to wait
   */
  wait: boolean = false;


  /**
   * Default constructor
   */
  constructor()
  {
    this.app = AppComponent.singleton;
  }


  /**
   * Initialize after view comes up
   */
  ngOnInit(): void
  {
  }


  /**
   * Submit a login request
   */
  public doLogin(): void
  {
    this.wait = true;
    AppComponent.singleton.api.sendLoginRequest(this.req, this.handleLoginResponse.bind(this));
  }


  /**
   * Handle a login response
   */
  public handleLoginResponse(response: LoginResponse): void
  {
    this.wait = false;

    if (response.ok)
    {
      /* save the JWT and refresh token */
      if (response.data)
        this.app.api.setCredentials(response.data.jwt, response.data?.refresh);
    }
    else
    {
      /* show any error messages to the user */
      // TODO: Show errors in a dialog
      console.log(response.errors);
    }

  }


  /**
   * Submit a password recovery request
   */
  public doRecover(): void
  {
  }
}


/**
 * Login request interface
 */
export interface LoginRequest
{
  email: string;
  password: string;
}
