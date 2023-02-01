.. _installation:

*******************
System Installation
*******************

Introduction
============

The WRF Cloud framework can be installed in any AWS account via `CloudShell <https://aws.amazon.com/cloudshell>`_.

.. _permissions:

Required Permissions
====================

The user installing WRF Cloud must have sufficient administrative permissions within their AWS account. The required type of permissions are indicated for each installation step described below. Please work with the adminstrator of your AWS account to secure the required permissions.

Check existing permissions:

* In the **AWS Management Console**, use the top-level search bar to find and launch **IAM** for the AWS Identity and Access Management (IAM) Service.
* In **Access management > Users**, find your user name, and inspect the **Permissions policies**.
* Check that you have full **AdministratorAccess** or work with your AWS account administrator to add the following permissions policies:
   * TODO: list full set of required permissions

Prerequisites
=============

1. Login to the `AWS Management Console <https://aws.amazon.com/console>`_ for your account.
2. Check user permissions (see :numref:`permissions`).
3. Check for `Route 53 <https://aws.amazon.com/route53>`_ domain name.

   * Use the top-level search bar to find and launch the AWS **Route 53** Service.
   * Check for at least one **Hosted zone** or create a new one with an annual fee.

4. Check account limits.

   * Use the top-level search bar to find and launch the AWS **EC2** Service.
   * Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
   * Select **Limits** from the left navigation menu and search for **HPC** to find **Running On-Demand All HPC instances**.
   * If the **Current limit** is less than **96 vCPUs**, contact AWS to request an **AWS Service Quota** increase.

5. Check Simple Email Service.

   * Use the top-level search bar to find and launch the AWS **SES** Service.
   * Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
   * If you see a banner message warning that **Your Amazon SES account is in the sandbox in US East (Ohio)**, contact AWS to **Request production access**.

Procedures for initial installation
===================================

1. Login to the `AWS Management Console <https://aws.amazon.com/console>`_ for your account.
2. Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
3. Click the CloudShell icon at the top of the screen to start CloudShell.

.. figure:: figure/cloudshell_icon.png

4. Copy and paste the following into CloudShell terminal:

.. code-block:: ini

  git clone --branch feature/auto-install https://github.com/NCAR/wrfcloud
  ./wrfcloud/install_bootstrap.sh

The bootstrap script takes about 25 minutes to complete and is followed by a series of interactive questions and settings before WRF Cloud is installed. The default setting is provided in sqaure braces after each question. Simply hit enter to accept the default or modify the setting as needed. These questions include:

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
   * Choose an item from **Stack name** column and select the **Events** tab to monitor progress.

7. When installation completes, a log message in the **CloudShell** window directs you to the newly created WRF Cloud URL.

Procedures to uninstall the application
=======================================

* Remove data from S3 bucket named wrfcloud-XXXXXXX (do not remove the bucket as CloudFormation will handle this)
* Remove the wrfcloud_parallelcluster IAM policy
* Remove the AMI from the EC2 service (be sure to deregister the AMI and delete the snapshots!)
* Remove the SSH key from the EC2 service named wrfcloud-admin
* Remove the SES email identity for your admin's email address
* Delete CloudFormation stacks: WrfIntelImageBuilder, WrfCloudWebApp
* Wait for WrfCloudWebApp stack to finish deleting.  If a delete fails, delete it again, and DO NOT retain the resources.
* Delete WrfCloudApiData, WrfCloudWebCertificate (us-east-1)
