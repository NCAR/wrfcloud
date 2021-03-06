.. _administration:

*********************
System Administration
*********************

Adding Users
============

User Permissions
================

Audit Logs
==========
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
