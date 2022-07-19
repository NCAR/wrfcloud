import {Component, OnInit} from '@angular/core';
import {AppComponent} from "../app.component";
import {LoginRequest, LoginResponse} from "../client-api";

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.sass']
})
export class LoginComponent implements OnInit
{
  /**
   * Reference to the main application singleton
   */
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
   * Flag that tells us if we are waiting for a response from the API
   */
  busy: boolean = false;


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
    this.busy = true;
    AppComponent.singleton.api.sendLoginRequest(this.req, this.handleLoginResponse.bind(this));
  }


  /**
   * Handle a login response
   */
  public handleLoginResponse(response: LoginResponse): void
  {
    this.busy = false;

    if (response.ok)
    {
      /* save the JWT and refresh token */
      if (response.data)
      {
        this.app.api.setCredentials(response.data.jwt, response.data?.refresh);
        this.app.user = response.data.user;
      }

      /* rebuild the menus */
      this.app.buildMenu();
    }
    else
    {
      /* show any error messages to the user */
      this.app.showErrorDialog(response.errors);
    }
  }


  /**
   * Submit a password recovery request
   */
  public doRecover(): void
  {
  }
}
