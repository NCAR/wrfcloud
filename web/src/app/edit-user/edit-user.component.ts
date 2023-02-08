import {Component, Inject, OnInit} from '@angular/core';
import {
  CreateUserRequest, CreateUserResponse,
  DeleteUserRequest,
  DeleteUserResponse,
  UpdateUserRequest,
  UpdateUserResponse,
  User
} from "../client-api";
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";
import {AppComponent} from "../app.component";

@Component({
  selector: 'app-edit-user',
  templateUrl: './edit-user.component.html',
  styleUrls: ['./edit-user.component.sass']
})
export class EditUserComponent implements OnInit
{
  /**
   * Available role options
   */
  public roles: any = [
    {value: 'readonly', displayName: 'Read-only'},
    {value: 'regular', displayName: 'Regular'},
    {value: 'maintainer', displayName: 'Maintainer'},
    {value: 'admin', displayName: 'Admin'}
  ];


  /**
   * Busy flag
   */
  public busy: boolean = false;


  /**
   * Application singleton
   */
  public app: AppComponent;


  /**
   * User to edit
   */
  public user: User;


  /**
   * A flag to tell us if we are editing an existing user or creating a new one
   */
  public edit: boolean;


  /**
   * A flag to tell us if we are editing an existing user or creating a new one
   */
  public create: boolean;


  /**
   * Copy data into the user object
   *
   * @param dialogRef
   * @param data
   */
  constructor(public dialogRef: MatDialogRef<EditUserComponent>, @Inject(MAT_DIALOG_DATA) public data: {user: User, edit: boolean})
  {
    /* get singleton */
    this.app = AppComponent.singleton;

    /* deep copy */
    this.user = JSON.parse(JSON.stringify(data.user));

    /* set the edit/create flag */
    this.edit = data.edit;
    this.create = !this.edit;
  }


  ngOnInit(): void
  {
  }


  /**
   * Submit the user updates to the server
   */
  public updateUserData(): void
  {
    this.busy = true;

    this.user.active = undefined;
    const request: UpdateUserRequest = {user: this.user};
    this.app.api.sendUpdateUserRequest(request, this.handleUpdateUserResponse.bind(this));
  }


  /**
   * Handle a response
   *
   * @param response
   */
  public handleUpdateUserResponse(response: UpdateUserResponse): void
  {
    this.busy = false;

    if (response.ok)
      this.dialogRef.close();
    else
      this.app.showErrorDialog(response.errors);
  }


  /**
   * Delete a user from the system
   */
  public deleteUser(): void
  {
    this.busy = true;

    const request: DeleteUserRequest = {email: this.user.email};
    this.app.api.sendDeleteUserRequest(request, this.handleDeleteUserResponse.bind(this));
  }


  /**
   * Handle a response
   *
   * @param response
   */
  public handleDeleteUserResponse(response: DeleteUserResponse): void
  {
    this.busy = false;

    if (response.ok)
      this.dialogRef.close();
    else
      this.app.showErrorDialog(response.errors);
  }


  /**
   * Create a new user in the system
   */
  public createUser(): void
  {
    this.busy = true;

    const request: CreateUserRequest = {user: this.user};
    this.app.api.sendCreateUserRequest(request, this.handleCreateUserResponse.bind(this));
  }


  /**
   * Handle a response
   *
   * @param response
   */
  public handleCreateUserResponse(response: CreateUserResponse): void
  {
    this.busy = false;

    if (response.ok)
      this.dialogRef.close();
    else
      this.app.showErrorDialog(response.errors);
  }
}
