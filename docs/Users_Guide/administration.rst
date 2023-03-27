.. _administration:

******************************
System Administration Overview
******************************

System Adminstration can broken down into two pieces: administration within AWS and administration of the WRF Cloud system. The primary administrator is the person who installed WRF Cloud on their AWS account.

WRF Cloud is designed to be run and managed in a self-contained way, largely negating the need for accessing AWS itself. Following a successful installation of WRF Cloud, the primary administrator adds a user(s) to their WRF Cloud system with admin permissions. These admin users can then manage the access to WRF Cloud, without needing to access AWS. The system administration of WRF Cloud is described in the first section below. 

There may be times when the primary administrator may need to access AWS resources related to WRF Cloud to debug issues. The second section below includes some cursory information about AWS recourses that may be helpful. 

.. _wrfcloud_admin:

WRF Cloud Administration
========================

.. _roles:

User Roles & Permissions
------------------------

The following definitions and table describe the user roles and corresponding permissions for each role that exist in this framework.

* **anonymous:** Unknown user, will be prompted to sign up
* **readonly:** Active user who will view forecasts only
* **regular:** Active user who will schedule, launch, manage, and view forecasts
* **maintainer:** Active user in the system with permissions of a regular user and can also create or update new model configurations 
* **admin:** Active user with permissions of a maintainer and also admin permissions to manage users and the system

.. list-table:: Roles and Permissions
   :widths: 10 10 10 10 10 10
   :header-rows: 1
   
   * -   
     - admin
     - maintainer
     - regular
     - readonly
     - anonymous
   * - Change Password
     -   X
     -   X
     -   X
     -   X 
     -   
   * - View Forecasts 
     - X
     - X
     - X
     - X
     -  
   * - List jobs  
     - X
     - X
     - X
     - X
     -  
   * - Run and Schedule Forecasts
     -  X
     -  X
     -  X
     -    
     -   
   * - Cancel and Delete Jobs
     - X
     - X
     - X 
     -  
     -  
   * - Create and Update Model Configurations
     - X
     - X
     -  
     -  
     -  
   * - Manage Users  
     - X
     -   
     -  
     -  
     -  

.. _admin_manage_users:

Managing Users
--------------

Users with the **Admin** role have permission to manage the users on their system. Admin users will see the menu option "Manage Users" on their User Interface, which allows the admin to add new users, update active user roles, or delete users. Select the "Manage Users" menu option to view a current list of users. 

**Add a New User**

Select the "Manage Users" menu option and click on the "Add User" option at the top of the page. A pop-up box will appear to fill in the new user's email address and name. Select the Role for that user and click "Create". An email will be sent to the new user asking them to activate their account and setup a new password.

**Update Roles**

Select the "Manage Users" menu option to view a current list of users. Click on the user you wish to update. A pop-box box with the user's information will appear. Select the new role you wish to assign and click "Update". The user will automatically be given permissions associated with this new role. 

**Delete a User**

Select the "Manage Users" menu option to view a current list of users. Click on the user you wish to remove. A pop-box box with the user's information will appear. Click "Remove" to delete the user from the system.




.. _aws_admin:

AWS Administration
=====================

Audit Logs
----------
The API component will keep an audit log of every request received and store it in the
DynamoDB database table.  There is currently no plan to make these logs accessible via
the web application, but the log entries can be viewed via the AWS DynamoDB console at:
https://console.aws.amazon.com/dynamodb.

There are three main purposes for this audit log: 1) Help users to debug any problems they
may encounter.  If an action fails, the reference ID and any errors will be presented to the
user.  The reference ID can help an administrator to find the request details and the log
output from the request handler.  2) Keep a history of system activity.  This can help to
inform how the system is used and which users launched model jobs in the account.  3) The audit
logs can help to identify suspicious activity and from what IP the requests originate.

Each audit log entry represents a single API request and contains the following fields:

**Reference ID**: A unique ID for each request.  Entries can be found quickly by the reference
ID.

**Action**: The name of the action requested, which helps understand what the user was trying
to do.

**Authenticated**: A boolean flag that indicates if the request was from an authenticated user.

**Username**: The username or email address of the user that made the request, if authenticated.

**Client IP**: The IP address of the client that sent the request.

**Start Time**: The time that the request was received as seconds since 1970-01-01 00:00:00 UTC.

**End Time**: The time that the request handling finished.

**Duration**: The total amount of time in milliseconds that it took to handle the request.

**Action Success**: A boolean flat that indicates if the request was successful or failed.

CloudWatch Logs
---------------
The reference ID can be used to search the CloudWatch Logs to find logs leading up to an error, which may be useful to when debugging failures.
