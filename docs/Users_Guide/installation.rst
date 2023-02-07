.. _installation:

*******************
System Installation
*******************

Introduction
============

The WRF Cloud framework can be installed in any AWS account via `CloudShell <https://aws.amazon.com/cloudshell>`_.

If you encounter issues related to your AWS account, please work with your AWS account administrator. For issues related to the WRF Cloud installation, please post to `WRF Cloud GitHub Discussions <https://github.com/NCAR/wrfcloud/discussions>`_.

.. _permissions:

Required Permissions
====================

The user installing WRF Cloud must have sufficient administrative permissions within their AWS account. It is recommended to install with **AdministratorAccess**, **SystemAdministrator**, or root privileges. Please work with your AWS account administrator to secure the required permissions or find another user with sufficient permissions to perform the installation.

Check existing permissions:

* In the **AWS Management Console**, use the top-level search bar to find and launch the AWS **IAM** (Identity and Access Management) Service.
* If you are unable to launch the AWS **IAM** Service, you do not have sufficient permissions.
* In **Access management > Users**, find and select your user name, and inspect the **Permissions policies**.
* Ensure that you have **AdministratorAccess**, **SystemAdministrator**, or higher permissions.

If any of the following installation steps fail due to insufficient permissions, please contact your AWS account administrator for assistance.

.. _prerequisites:

Prerequisites
=============

The prerequisites for installing WRF Cloud in an AWS account are described below.

1. Login to the `AWS Management Console <https://aws.amazon.com/console>`_ for your account as a user with sufficient permissions (see :numref:`permissions`).

2. Check `Route 53 <https://aws.amazon.com/route53>`_ domain name.

   * Use the top-level search bar to find and launch the AWS **Route 53** Service.
   * Check for at least one **Hosted zone** or create a new one with an annual fee.

3. Check account limits.

   * Use the top-level search bar to find and launch the AWS **EC2** Service.
   * Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
   * Select **Limits** from the left navigation menu and search for **HPC** to find **Running On-Demand HPC instances**.
   * If the **Current limit** is less than **96 vCPUs**, select the radio button and click **Request limit increase**.
   * Check your email for followup and confirmation from AWS support.

4. Check Simple Email Service (SES).

   * Use the top-level search bar to find and launch the AWS **SES** Service.
   * Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
   * If you registered a new **Route 53** domain above, you'll need to create a new verified identity.

      * Select **Configuration > Verified identities** from the left navigation menu.
      * If the newly added domain is not listed, select the **Create identity** button, select the **Domain** radio button, and enter the newly added domain.
      * Check your email for followup and confirmation from AWS support.
      * Confirm that the newly added domain appears in the **Verified indentities** list.

   * If you see a banner message warning that **Your Amazon SES account is in the sandbox in US East (Ohio)**, contact AWS to **Request production access**.

      * Prior to requesting production access, be sure that you have at least one verified identity (see above).
      * Check your email for followup and confirmation from AWS support.
      * If AWS requires further justification for this change, note that this email service is needed by WRF Cloud to send users emails when WRF jobs finish running and to facilitate password recovery. We also recommend that your AWS account administrators subscribe to an SNS topic that is configured to accept bounce and complaint messages.

Procedures for initial installation
===================================

Once the AWS account prerequisites are satisfied (see :numref:`prerequisites`), follow these instructions to install WRF Cloud.

1. Login to the `AWS Management Console <https://aws.amazon.com/console>`_ for your account as a user with sufficient permissions (see :numref:`permissions`).

2. Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.

3. Click the CloudShell icon at the top of the screen to start CloudShell.

.. figure:: figure/cloudshell_icon.png

4. Copy and paste the following into CloudShell terminal:

.. code-block:: ini

  git clone https://github.com/NCAR/wrfcloud
  ./wrfcloud/install_bootstrap.sh

This command installs WRF Cloud using the current default branch of the repository. To install a specific tagged version or branch, specify its name as an agrument to the script (e.g. **./wrfcloud/install_bootstrap.sh v1.0**).

This bootstrap script takes about 25 minutes to run. It is followed by a series of interactive questions that must be completed prior to WRF Cloud being installed. For each question, the default option (if applicable) is provided in sqaure braces. Simply hit enter to accept the default or modify the setting as needed. These questions include:

* Would you like to enable autocompletion?
* Which domain name would you like to use? [e.g. wrfcloud.com]
* Enter host name for web application: [e.g. app.wrfcloud.com]
* Enter host name for REST API: [e.g. api.wrfcloud.com]
* Enter host name for websocket API: [e.g. ws.wrfcloud.com]
* Enter administrator's full name:
* Enter email address for application administrator:
* Enter administrator's new password:
* Do you want to install example model configurations? *Recommend Yes*
* Do you want to upload an SSH public key for an admin? *Recommend Yes*
* Paste your public key, often found at ${HOME}/.ssh/id_rsa.pub:

5. After completing these steps, check the email address provided above to verify it. It takes approximately 10-20 minutes for the website to become available.

6. Monitor the installation progress:

   * Use the top-level search bar to find and launch the AWS **CloudFormation** Service.
   * Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
   * Select **Stack** from the left navigation menu.
   * Choose an item from **Stack name** column and select the **Events** tab to monitor progress.

7. When installation completes, a log message in the **CloudShell** window directs you to the newly created WRF Cloud URL.

Procedures to uninstall the application
=======================================

The steps for uninstalling WRF Cloud from an AWS account are described below.

* Remove data from S3 bucket named wrfcloud-XXXXXXX (do not remove the bucket as CloudFormation will handle this).
* Remove the wrfcloud_parallelcluster IAM policy.
* Remove the AMI from the EC2 service (be sure to deregister the AMI and delete the snapshots!).
* Remove the SSH key from the EC2 service named wrfcloud-admin.
* Remove the SES email identity for your admin's email address.
* Delete CloudFormation stacks: WrfIntelImageBuilder, WrfCloudWebApp.
* Wait for WrfCloudWebApp stack to finish deleting.  If a delete fails, delete it again, and DO NOT retain the resources.
* Delete WrfCloudApiData, WrfCloudWebCertificate (us-east-1).
