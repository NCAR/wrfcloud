import {Component, OnInit} from '@angular/core';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.sass']
})
export class LoginComponent implements OnInit
{
  /**
   * Initialize an empty login request
   */
  req: LoginRequest = {email: '', password: ''};


  /**
   * Flag to switch displays to the i-forgot-my-password mode
   */
  iForgot: boolean = false;


  /**
   * Default constructor
   */
  constructor()
  {
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
