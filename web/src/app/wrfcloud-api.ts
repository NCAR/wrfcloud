/**
 * Collection of API functions
 */
import {HttpClient} from "@angular/common/http";


export class WrfCloudApi
{
  /**
   * JSON Web Token
   */
  public jwt: string|undefined|null;


  /**
   * Refresh token
   */
  public refreshToken: string|undefined|null;


  /**
   * Expiration time of the JWT
   */
  public expires: number|undefined|null;


  /**
   * Email address of the user
   */
  public email: string|undefined|null;


  /**
   * Flag to tell us if we have valid credentials
   */
  public loggedIn: boolean = false;


  /**
   * Construct a new API object
   *
   * @param http Angular's HttpClient
   */
  constructor(public http: HttpClient)
  {
    this.loadCredentials();
  }


  /**
   * A URL to the API
   */
  // public API_URL = 'https://api-dev.wrfcloud.com/v1/action';
  // public API_URL = 'https://api.wrfcloud.com/v1/action';
  public API_URL = 'https://wrfcloudapi.superlazy.org/v1/action';


  /**
   * Set new credentials
   * @param jwt JSON Web Token
   * @param refreshToken Refresh token
   */
  public setCredentials(jwt: string, refreshToken: string): void
  {
    this.jwt = jwt;
    this.refreshToken = refreshToken;
    this.expires = this.getJwtExpiration();

    /* call refresh token automatically before the token expires */
    if (this.expires && this.email)
    {
      const remainingMs = (this.expires * 1000) - new Date().getTime() - 60000;
      const req: RefreshTokenRequest = {email: this.email, refresh_token: this.refreshToken};
      const handler: Function = this.handleRefreshTokenResponse.bind(this);
      setTimeout(this.sendRefreshTokenRequest.bind(this), remainingMs, req, handler);
    }

    /* save credentials to local storage */
    WrfCloudApi.saveCredentials(jwt, refreshToken);

    /* set the logged in flag */
    this.loggedIn = (this.jwt !== undefined && this.refreshToken !== undefined);
  }


  /**
   * Save credentials to local storage
   */
  private static saveCredentials(jwt: string, refreshToken: string): void
  {
    localStorage.setItem('wrfcloud_jwt', jwt);
    localStorage.setItem('wrfcloud_refresh', refreshToken);
  }


  /**
   * Load credentials from local storage (if any)
   */
  private loadCredentials(): void
  {
    this.jwt = localStorage.getItem('wrfcloud_jwt');
    this.refreshToken = localStorage.getItem('wrfcloud_refresh');
    this.expires = this.getJwtExpiration();
    this.email = this.getJwtEmail();

    if (this.jwt && this.refreshToken)
      this.setCredentials(this.jwt, this.refreshToken);
  }


  /**
   * Logout of the system
   */
  public logout(): void
  {
    this.jwt = undefined;
    this.refreshToken = undefined;
    this.expires = undefined;
    this.email = undefined;
    this.loggedIn = false;

    localStorage.removeItem('wrfcloud_jwt');
    localStorage.removeItem('wrfcloud_refresh');
  }


  /**
   * Parse the expiration time from the JWT
   * @private
   */
  private getJwtExpiration(): number|undefined
  {
    if (this.jwt === undefined || this.jwt === null)
      return undefined;

    return JSON.parse(atob(this.jwt.split('.')[1]))['expires'];
  }


  /**
   * Parse the email address from the JWT
   * @private
   */
  private getJwtEmail(): string|undefined
  {
    if (this.jwt === undefined || this.jwt === null)
      return undefined;

    return JSON.parse(atob(this.jwt.split('.')[1]))['email'];
  }


  /**
   * Send a request to the API
   * @param request
   * @param responseHandler
   * @private
   */
  private sendRequest(request: ApiRequest, responseHandler: Function): void
  {
    /* prepare the request headers */
    const options = {'headers': {
      'Content-Type': 'application/json'
    }};

    /* send the POST request */
    this.http.post(this.API_URL, request, options).subscribe((event: Object) => {
      responseHandler(event);
    });
  }


  /**
   * Send a login request
   *
   * @param requestData
   * @param responseHandler
   */
  public sendLoginRequest(requestData: LoginRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'Login',
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler);
  }


  /**
   * Send a change password request
   *
   * @param requestData
   * @param responseHandler
   */
  public sendChangePasswordRequest(requestData: ChangePasswordRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'ChangePassword',
      jwt: this.jwt,
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler);
  }


  /**
   * Send a user data request
   *
   * @param responseHandler
   */
  public sendWhoAmIRequest(responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'WhoAmI',
      jwt: this.jwt,
      data: {}
    };

    /* send the API request */
    this.sendRequest(request, responseHandler);
  }


  /**
   * Send a refresh token request
   * @param requestData
   * @param responseHandler
   */
  public sendRefreshTokenRequest(requestData: RefreshTokenRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'RefreshToken',
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler);
  }


  /**
   * Handle a response from a refresh token request
   * @param response
   */
  public handleRefreshTokenResponse(response: RefreshTokenResponse): void
  {
    if (response.ok && response.data !== undefined)
    {
      this.setCredentials(response.data.jwt, response.data.refresh);
    }
  }
}


/**
 * User object
 */
export interface User
{
  email: string;
  full_name: string;
  role_id: string;
}


/**
 * All API requests will have an action, and maybe a token and data.
 */
export interface ApiRequest
{
  action: string;
  jwt?: string|undefined|null;
  data?: Object;
}


/**
 * Every API response will have an ok flag, indicating success or failure.
 * If the request failed, then a list of error messages will also be present.
 */
export interface ApiResponse
{
  ok: boolean;
  errors?: Array<string>;
}


/**
 * Login request interface
 */
export interface LoginRequest
{
  email: string;
  password: string;
}


/**
 * Login response will include a data section if request is successful.
 */
export interface LoginResponse extends ApiResponse
{
  data?: {
    jwt: string;
    refresh: string;
    user: User;
  }
}


/**
 * Refresh token request
 */
export interface RefreshTokenRequest
{
  email: string;
  refresh_token: string;
}


/**
 * Refresh token response
 */
export interface RefreshTokenResponse extends LoginResponse
{
  /* same as LoginResponse */
}


/**
 * Change password request
 */
export interface ChangePasswordRequest
{
  password0: string;
  password1: string;
  password2: string;
}


/**
 * Change password response
 */
export interface ChangePasswordResponse extends ApiResponse
{
}


/**
 * Who Am I response
 */
export interface WhoAmIResponse extends ApiResponse
{
  data: {
    user: User;
  }
}
