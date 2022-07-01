import {Component, AfterViewInit, OnInit, ViewChild} from '@angular/core';
import {AppComponent} from "../app.component";
import {ListUsersResponse, User} from "../wrfcloud-api";
import {MatSort} from "@angular/material/sort";
import {MatTableDataSource} from "@angular/material/table";
import {MatPaginator} from "@angular/material/paginator";
import {MatDialog} from "@angular/material/dialog";
import {EditUserComponent} from "../edit-user/edit-user.component";

@Component({
  selector: 'app-manage-users',
  templateUrl: './manage-users.component.html',
  styleUrls: ['./manage-users.component.sass']
})
export class ManageUsersComponent implements OnInit, AfterViewInit
{
  // @ts-ignore
  @ViewChild(MatSort) sort: MatSort;
  // @ts-ignore
  @ViewChild(MatPaginator) paginator: MatPaginator;


  /**
   * Application singleton
   */
  public app: AppComponent;


  /**
   * Search filter for the data table
   */
  public filter: string = '';


  /**
   * Indicates loading data from API
   */
  public busy: boolean = false;


  /**
   * List of users
   */
  public users: Array<User> = [];


  /**
   * Table data
   */
  public dataSource: MatTableDataSource<User> = new MatTableDataSource<User>([]);


  /**
   * Column names to display on a desktop computer
   */
  public desktopColumns: Array<string> = ['active', 'full_name', 'email', 'role_id'];


  /**
   * Column names to display on a mobile device
   */
  public mobileColumns: Array<string> = ['full_name', 'email'];


  /**
   * Refresh data
   */
  constructor(public dialog: MatDialog)
  {
    /* get the application singleton */
    this.app = AppComponent.singleton;

    /* load a list of users */
    this.loadUserList();
  }


  /**
   *
   */
  ngOnInit(): void
  {
  }


  /**
   * Grab the table paginator and sorter
   */
  ngAfterViewInit()
  {
    this.dataSource.sort = this.sort;
    this.dataSource.paginator = this.paginator;
  }


  /**
   * Load a list of users from the server
   */
  public loadUserList(): void
  {
    this.busy = true;

    this.app.api.sendListUsersRequest(this.handleUserListResponse.bind(this));
  }


  /**
   * Handle a response from list users
   * @param response
   */
  public handleUserListResponse(response: ListUsersResponse): void
  {
    this.busy = false;

    if (response.ok)
    {
      /* save the user list */
      this.users = response.data.users;
      this.dataSource.data = this.users;
    }
    else
    {
      /* show errors */
      this.app.showErrorDialog(response.errors);
    }
  }


  /**
   * Handle an event where the user clicks on a row in the table
   *
   * @param user User object for the row clicked
   */
  public userClicked(user: User): void
  {
    const editData: {user: User, edit: boolean} = {
      user: user,
      edit: true
    };

    this.dialog.open(EditUserComponent, {data: editData}).afterClosed().subscribe(
      () => { this.loadUserList(); }
    );
  }


  /**
   * Apply the search filter to the table items
   */
  public filterModified(): void
  {
    this.dataSource.filter = this.filter;
  }


  /**
   * Add a new user
   */
  public addUser(): void
  {
    const editData: {user: User, edit: boolean} = {
      user: {full_name: '', email: '', role_id: 'readonly'},
      edit: false
    };

    this.dialog.open(EditUserComponent, {data: editData}).afterClosed().subscribe(
      () => { this.loadUserList(); }
    );
  }
}
