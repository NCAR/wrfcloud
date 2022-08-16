import {Component, OnInit} from '@angular/core';
import {AppComponent} from "../app.component";
import {LoginRequest, LoginResponse, PasswordRecoveryTokenRequest, PasswordRecoveryTokenResponse} from "../client-api";


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
   * Flag to indicate successful email send for password recovery token
   */
  showRecoveryInstructions: boolean = false;


  /**
   * Wait interval between requesting password recovery tokens
   */
  recoveryWaitSeconds: number = 600;


  /**
   * Remaining wait time for new recovery email
   */
  recoveryRemainingSeconds: number = this.recoveryWaitSeconds;


  /**
   * Remaining minutes estimated for display
   */
  recoveryRemainingMinutes: number = 0;


  /**
   * Wait start time
   */
  recoveryWaitStart: Date|undefined;


  /**
   * Wait progress 0-100 for
   */
  recoveryWaitProgress: number = 0;


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
   *
   * @param response API response
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
    this.busy = true;
    const request: PasswordRecoveryTokenRequest = {email: this.req.email};
    AppComponent.singleton.api.sendPasswordRecoveryTokenRequest(request, this.handleRecoveryResponse.bind(this));
  }


  /**
   * Handle a password recovery response
   *
   * @param response API response
   */
  public handleRecoveryResponse(response: PasswordRecoveryTokenResponse): void
  {
    this.busy = false;

    if (response.ok)
    {
      this.showRecoveryInstructions = true;
      this.recoveryWaitSeconds = response.data.wait_interval_seconds;
      this.recoveryWaitStart = new Date();
      this.runRecoveryTimer();
    }
    else
    {
      this.app.showErrorDialog(response.errors);
    }
  }


  /**
   * Update progress bar and eventually reset the UI
   */
  public runRecoveryTimer(): void
  {
    /* make sure we are in a waiting state */
    if (this.recoveryWaitStart === undefined)
      return;

    /* calculate the remaining seconds */
    const now = new Date();
    const elapsedSeconds = (now.getTime() - this.recoveryWaitStart.getTime()) / 1000;
    this.recoveryRemainingSeconds = this.recoveryWaitSeconds - (elapsedSeconds);
    this.recoveryRemainingMinutes = Math.round((this.recoveryRemainingSeconds / 60) + 0.499999);

    /* set the progress bar value */
    this.recoveryWaitProgress = 100 - (this.recoveryRemainingSeconds * 100 / this.recoveryWaitSeconds);

    /* if we are still waiting, compute values again in a second */
    if (this.recoveryRemainingSeconds > 0)
    {
      setTimeout(this.runRecoveryTimer.bind(this), 1000);
    }
    else
    {
      this.showRecoveryInstructions = false;
    }
  }
}
