/**
 * Collection of API functions
 */
import {HttpClient} from "@angular/common/http";
import {Layer} from "ol/layer";
import {HostConfig} from "./host-config";


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
  public static API_URL = 'https://' + HostConfig.API_HOSTNAME + '/v1/action';
  public static WEBSOCKET_URL = 'wss://' + HostConfig.WS_HOSTNAME + '/v1';


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
   * Send a request for WRF meta data
   *
   * @param requestData
   * @param responseHandler
   */
  public sendGetWrfMetaDataRequest(requestData: GetWrfMetaDataRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'GetWrfMetaData',
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, true);
  }


  /**
   * Send a request for WRF geojson data
   *
   * @param requestData
   * @param responseHandler
   */
  public sendGetWrfGeoJsonRequest(requestData: GetWrfGeoJsonRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'GetWrfGeoJson',
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, true);
  }


  /**
   * Send a list user request
   *
   * @param requestData
   * @param responseHandler
   */
  public sendListJobsRequest(requestData: ListJobRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'ListJobs',
      data: requestData
    };

    /* send the API request */
    this.sendRequest(request, responseHandler, true);
  }


  /**
   * Launch a WRF run
   */
  public sendLaunchWrf(requestData: RunWrfRequest, responseHandler: Function): void
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'RunWrf',
      data: requestData
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
      console.log('wsconn');
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
    {
      const tempsocket = this.websocket;
      this.websocket = undefined;
      tempsocket.close();
    }
  }


  /**
   * Send a subscription message
   *
   * @return False if the message was not sent
   */
  public subscribeToJobChanges(): boolean
  {
    /* create the API request */
    const request: ApiRequest = {
      action: 'SubscribeJobs',
      data: {}
    };

    /* send the API request */
    return this.sendWebsocketMessage(request, true);
  }


  /**
   * Send a message to the websocket
   * @private
   *
   * @param message The message to send to the API via websocket
   * @param includeJwt Should the jwt be attached to the message before sending
   * @return True if the message was sent, otherwise false
   */
  private sendWebsocketMessage(message: ApiRequest, includeJwt: boolean): boolean
  {
    /* maybe add the JWT to the message */
    if (includeJwt)
      message.jwt = this.jwt;

    /* check if the websocket is still connected */
    if (this.websocket !== undefined && this.websocket.readyState === WebSocket.OPEN)
    {
      this.websocket.send(JSON.stringify(message));
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
  palette_name: string;
  min_value: number;
  max_value: number;
}

export interface WrfLayerGroup
{
  layers: {[z_level: number]: WrfLayer[]};
  palette: Palette;
  units: string;
  loaded: number;
  progress: number;
  variable_name: string;
  display_name: string;
  opacity: number;
  visible: boolean;
  visibilityChange: Function;
  opacityChange: Function;
}

export interface WrfLayer
{
  variable_name: string;
  display_name: string;
  palette: Palette;
  units: string;
  visible: boolean;
  opacity: number;
  layer_data: string|Layer;
  z_level: number;
  time_step: number;
  dt: number;
}

export interface WrfJob
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
  user_email: string;
  notify: boolean;
  layers: Array<WrfLayer>;
  domain_center: LatLonPoint;
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

export interface GetWrfMetaDataRequest
{
}

export interface GetWrfMetaDataResponse extends ApiResponse
{
  data: {
    configurations: Array<WrfMetaDataConfiguration>;
  }
}

export interface WrfMetaDataConfiguration
{
  configuration_name: string;
  cycle_times: Array<WrfMetaDataCycleTime>;
}

export interface WrfMetaDataCycleTime
{
  cycle_time: number;
  valid_times: Array<number>
}

export interface GetWrfGeoJsonRequest
{
  job_id: string;
  valid_time: number;
  variable: string;
  z_level: number;
}

export interface GetWrfGeoJsonResponse extends ApiResponse
{
  data: {
    job_id: string;
    valid_time: number;
    variable: string;
    z_level: number;
    geojson: string
  }
}

export interface ListJobRequest
{
  job_id?: string;
}

export interface ListJobResponse extends ApiResponse
{
  data: {
    jobs: WrfJob[];
  }
}

// export interface Job
// {
//   job_id: string;
//   job_name: string;
//   configuration_name: string;
//   cycle_time: number;
//   forecast_length: number;
//   output_frequency: number;
//   status_code: number;
//   status_message: string;
//   progress: number;
// }

export interface WebsocketListener
{
  websocketOpen: (event: Event) => void;
  websocketClose: (event: CloseEvent) => void;
  websocketMessage: (event: MessageEvent) => void;
}

export interface WebsocketMessage
{
  type: string;
  data: ApiResponse;
}

export interface JobStatusResponse extends ApiResponse
{
  data: {
    job: WrfJob
  }
}

export interface RunWrfRequest
{
  job_name: string;
  configuration_name: string;
  start_time: number;
  forecast_length: number;
  output_frequency: number;
  notify: boolean;
}

export interface RunWrfResponse extends ApiResponse
{
  data: {
    ref_id: string;
  }
}
