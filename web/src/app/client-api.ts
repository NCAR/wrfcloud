/**
 * Collection of API functions
 */
import {HttpClient} from "@angular/common/http";


export class ClientApi
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
   * Websocket connected to the WRF Cloud websocket service
   * @private
   */
  private websocket: WebSocket|undefined;


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
  public static API_URL = 'https://api.wrfcloud.com/v1/action';
  // public static WEBSOCKET_URL = 'wss://ws.wrfcloud.com/default/v1';
  public static WEBSOCKET_URL = 'wss://qf4es7tvh4.execute-api.us-east-2.amazonaws.com/v1';


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
    ClientApi.saveCredentials(jwt, refreshToken);

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
   * Determine if the JSON Web Token is expired
   * @private
   */
  private jwtExpired(): boolean
  {
    /* get current timestamp */
    const now: number = new Date().getTime() / 1000;

    /* check if we have a JWT with expiry date */
    if (this.expires === undefined || this.expires === null)
      return false;

    /* check if JWT is already expired */
    if (this.expires < now)
      return true;

    /* token is not expired */
    return false;
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
   * @param includeJwt
   * @private
   */
  private sendRequest(request: ApiRequest, responseHandler: Function, includeJwt: boolean): void
  {
    /* ensure we have a non-expired JWT */
    if (includeJwt && this.loggedIn && this.jwtExpired())
    {
      /* refresh the JWT */
      if (this.email !== undefined && this.email !== null && this.refreshToken !== undefined && this.refreshToken !== null)
      {
        const req: RefreshTokenRequest = {email: this.email, refresh_token: this.refreshToken};
        this.sendRefreshTokenRequest(req, this.handleRefreshTokenResponse.bind(this));
      }

      /* defer this request */
      setTimeout(this.sendRequest.bind(this), 1000, request, responseHandler, includeJwt);

      /* this function will get called again in 1 second */
      return;
    }

    /* prepare the request headers */
    const options = {'headers': {
      'Content-Type': 'application/json'
    }};

    /* maybe add the JWT */
    if (includeJwt)
      request.jwt = this.jwt;

    /* send the POST request */
    this.http.post(ClientApi.API_URL, request, options).subscribe((event: Object) => {
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
    this.sendRequest(request, responseHandler, false);
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
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, true);
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
      data: {}
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, true);
  }


  /**
   * Send a list user request
   *
   * @param responseHandler
   */
  public sendListUsersRequest(responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'ListUsers',
      data: {}
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, true);
  }


  /**
   * Send an update user request
   *
   * @param requestData
   * @param responseHandler
   */
  public sendUpdateUserRequest(requestData: UpdateUserRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'UpdateUser',
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, true);
  }


  /**
   * Send a delete user request
   *
   * @param requestData
   * @param responseHandler
   */
  public sendDeleteUserRequest(requestData: DeleteUserRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'DeleteUser',
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, true);
  }


  /**
   * Send a create user request
   *
   * @param requestData
   * @param responseHandler
   */
  public sendCreateUserRequest(requestData: CreateUserRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'CreateUser',
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, true);
  }


  /**
   * Send a create user request
   *
   * @param requestData
   * @param responseHandler
   */
  public sendActivateUserRequest(requestData: ActivateUserRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'ActivateUser',
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, false);
  }


  /**
   * Send a request for a password recovery token by email
   *
   * @param requestData
   * @param responseHandler
   */
  public sendPasswordRecoveryTokenRequest(requestData: PasswordRecoveryTokenRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'RequestPasswordRecoveryToken',
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, false);
  }


  /**
   * Send a reset password request
   *
   * @param requestData
   * @param responseHandler
   */
  public sendResetPasswordRequest(requestData: ResetPasswordRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'ResetPassword',
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, false);
  }


  /**
   * Send a list user request
   *
   * @param responseHandler
   */
  public sendListJobsRequest(responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'ListJobs',
      data: {}
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, true);
  }


  /**
   * Send a refresh token request
   *
   * @param requestData
   * @param responseHandler
   */
  public sendRefreshTokenRequest(requestData: RefreshTokenRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'RefreshToken',
      jwt: this.jwt,
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, false);
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


  /**
   * Open a websocket connection
   */
  public connectWebsocket(listener: WebsocketListener): void
  {
    if (this.websocket === undefined || this.websocket.readyState === WebSocket.CLOSED)
    {
      this.websocket = new WebSocket(ClientApi.WEBSOCKET_URL);
      this.websocket.onopen = listener.websocketOpen.bind(listener);
      this.websocket.onclose = listener.websocketClose.bind(listener);
      this.websocket.onmessage = listener.websocketMessage.bind(listener);
    }
  }


  /**
   * Disconnect from the websocket connection -- costs are incurred partially
   * by time connected, so it is good to disconnect when not necessary.
   */
  public disconnectWebsocket(): void
  {
    if (this.websocket !== undefined && this.websocket.readyState !== WebSocket.CLOSED)
      this.websocket.close();
  }


  /**
   * Send a message to the websocket
   *
   * @param msg
   */
  public sendWebsocket(msg: Object): boolean
  {
    if (this.websocket !== undefined && this.websocket.readyState === WebSocket.OPEN)
    {
      console.log('Websocket Send Message:');
      console.log(msg);
      this.websocket.send(JSON.stringify(msg));
      return true;
    }
    return false;
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
  active?: boolean;
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
    user: User
  }
}


/**
 * List user response
 */
export interface ListUsersResponse extends ApiResponse
{
  data: {
    users: Array<User>
  }
}

export interface UpdateUserRequest
{
  user: User;
}

export interface UpdateUserResponse extends ApiResponse
{
}

export interface DeleteUserRequest
{
  email: string;
}

export interface DeleteUserResponse extends ApiResponse
{
}

export interface CreateUserRequest
{
  user: User
}

export interface CreateUserResponse extends ApiResponse
{
}

export interface ActivateUserRequest
{
  email: string;
  activation_key: string;
  new_password: string;
}

export interface ActivateUserResponse extends ApiResponse
{
}

export interface LatLonPoint
{
  latitude: number;
  longitude: number;
}

export interface Palette
{
  name: string;
  min: number;
  max: number;
}

export interface WrfLayer
{
  name: string;
  displayName: string;
  palette: Palette;
  units: string;
  visible: boolean;
  opacity: number;
  data?: any;
}

export interface WrfJob
{
  name: string;
  domainCenter: LatLonPoint;
  layers: WrfLayer[];
  initializationTime: string[];
}

export interface LayerRequest
{
  height: number;
}

export interface PasswordRecoveryTokenRequest
{
  email: string;
}

export interface PasswordRecoveryTokenResponse extends ApiResponse
{
  data: {
    wait_interval_seconds: number
  }
}

export interface ResetPasswordRequest
{
  email: string;
  reset_token: string;
  new_password: string;
}

export interface ResetPasswordResponse extends ApiResponse
{
}

export interface ListJobResponse extends ApiResponse
{
  data: {
    jobs: Job[];
  }
}

export interface Job
{
  job_id: string;
  job_name: string;
  configuration_name: string;
  cycle_time: number;
  forecast_length: number;
  output_frequency: number;
  status_code: number;
  status_message: string;
  progress: number;
}

export interface WebsocketListener
{
  websocketOpen: (event: Event) => void;
  websocketClose: (event: CloseEvent) => void;
  websocketMessage: (event: MessageEvent) => void;
}
