import {Component, Inject, OnInit} from '@angular/core';
import {UpdateUserRequest, UpdateUserResponse, User} from "../wrfcloud-api";
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";
import {AppComponent} from "../app.component";
import {AppModule} from "../app.module";

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
    {value: 'admin', displayName: 'Admin'}
  ];


  /**
   * Application singleton
   */
  public app: AppComponent;


  /**
   * User to edit
   */
  public user: User;


  /**
   * Copy data into the user object
   *
   * @param dialogRef
   * @param data
   */
  constructor(public dialogRef: MatDialogRef<EditUserComponent>, @Inject(MAT_DIALOG_DATA) public data: User)
  {
    /* get singleton */
    this.app = AppComponent.singleton;

    /* deep copy */
    this.user = JSON.parse(JSON.stringify(data));
  }


  ngOnInit(): void
  {
  }


  /**
   * Submit the user updates to the server
   */
  public updateUserData(): void
  {
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
    if (response.ok)
      this.dialogRef.close();
    else
      this.app.showErrorDialog(response.errors);
  }
}
