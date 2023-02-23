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

The are 4 prerequisites for installing WRF Cloud in an AWS account:

* **Web Domain**: This is the web domain (hosted zone) where the WRF Cloud system is accessed. AWS's `Route 53 <https://aws.amazon.com/route53>`_ Domain Naming Service (DNS) is used to create and host the domain for the system. This service has an annual cost associated with it.
* **Adequate Instance Limits**: On-demand HPC instance limits must be set to a minimum of 96 vCPUs. By default, the AWS account may be less than this. A request should be made to increase this limit for full functionality of the system.
* **Enable Simple Email Service (SES)**: This facilitates AWS emailing within the system. By default the SES is limited to testing with verified identities. A request must be made to lift these limits and make it a production service.
* **Access to us-east-2 region**: The hpc6a instances that the system uses are only available in the us-east-2 region. This is typically available by default for regular AWS accounts.

The procedures for ensuring the prerequisites are fulfilled are described below.

1. Login to the `AWS Management Console <https://aws.amazon.com/console>`_ for your account as a user with sufficient permissions (see :numref:`permissions`).
   
2. Check `Route 53 <https://aws.amazon.com/route53>`_ domain name.

   * Use the top-level search bar to find and launch the AWS **Route 53** Service.
   * Check for at least one **Hosted zone** or create a new one with an annual fee.

3. Check account limits.

   * Use the top-level search bar to find and launch the AWS **EC2** Service.
   * Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
      * Access to us-east-2 region is required. This is likely enabled by default, per AWS documentation for standard AWS accounts. In the event that you do not see us-east-2 region as an option when going through the procedures, contact you AWS account administrator, or AWS directly, to inquire about enabling it. 
   * Select **Limits** from the left navigation menu and search for **HPC** to find **Running On-Demand HPC instances**.
   * If the **Current limit** is less than **96 vCPUs**, select the radio button and click **Request limit increase**.
   * **AWS Support Center** will followup via email with the AWS account owner.

     * See details about contacting `AWS Support Center <https://docs.aws.amazon.com/awssupport/latest/user/accessing-support.html>`_, as needed.

4. Check Simple Email Service (SES).

   * Use the top-level search bar to find and launch the AWS **SES** Service.
   * Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
   * If you registered a new **Route 53** domain above, you'll need to create a new verified identity.

      * Select **Configuration > Verified identities** from the left navigation menu.
      * If the newly added domain is not listed, select the **Create identity** button, select the **Domain** radio button, and enter the newly added domain.
      * `AWS Support Center <https://docs.aws.amazon.com/awssupport/latest/user/accessing-support.html>`_ will followup via email with the AWS account owner.
      * Confirm that the newly added domain appears in the **Verified identities** list.

   * If you see a banner message warning that **Your Amazon SES account is in the sandbox in US East (Ohio)**, contact AWS to **Request production access**.

      * Prior to requesting production access, be sure that you have at least one verified identity (see above).
      * `AWS Support Center <https://docs.aws.amazon.com/awssupport/latest/user/accessing-support.html>`_ will followup via email with the AWS account owner.
      * If AWS requires further justification for this change, note that this email service is needed by WRF Cloud to send users emails when WRF jobs finish running and to facilitate password recovery. We also recommend that your AWS account administrators subscribe to an SNS topic that is configured to accept bounce and complaint messages.

.. _install:

Procedures to Install
=====================

Once the AWS account prerequisites are satisfied (see :numref:`prerequisites`), follow these instructions to install WRF Cloud.

1. Login to the `AWS Management Console <https://aws.amazon.com/console>`_ for your account as a user with sufficient permissions (see :numref:`permissions`).

2. Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.

3. Click the **CloudShell** button (|cloudshell_16x16|) at the top of the screen to launch a terminal window.

.. |cloudshell_16x16| image:: figure/cloudshell_icon.png
               :alt: CloudSell_Icon
               :height: 16px
               :width: 16px

4. Define the GitHub branch name (e.g. develop) or release name (e.g. v1.0) to be installed.

  .. code-block:: ini

    export GITHUB_NAME=develop

5. Copy and paste the following into the CloudShell terminal:

  .. code-block:: ini

    git clone --branch ${GITHUB_NAME} https://github.com/NCAR/wrfcloud
    ./wrfcloud/install_bootstrap.sh ${GITHUB_NAME}

This bootstrap script takes about 25 minutes to run. It is followed by a series of interactive questions that must be completed prior to WRF Cloud being installed. For each question, the default option (if applicable) is provided in square braces. Simply hit enter to accept the default or modify the setting as needed. These questions include:

  * Which domain name would you like to use? [`Route 53 <https://aws.amazon.com/route53>`_ domain(s) from :numref:`prerequisites`]

     * Note: This is used for {DOMAIN} in the following questions.

  * Enter host name for web application: [e.g. app.{DOMAIN}]
  * Enter host name for REST API: [e.g. api.{DOMAIN}]
  * Enter host name for websocket API: [e.g. ws.{DOMAIN}]
  * Enter administrator's full name:
  * Enter email address for application administrator:
  * Enter administrator's new password:
  * Do you want to install example model configurations? [*Recommend Yes*]
  * Do you want to upload an SSH public key for an admin? [*Recommend Yes*]
  * Paste your public key, often found at ${HOME}/.ssh/id_rsa.pub:

    * Copy and paste the output of this command into the CloudShell terminal:

      .. code-block:: ini

        cat ${HOME}/.ssh/id_rsa.pub

      If this file does not exist, refer to `this documentation <https://git-scm.com/book/en/v2/Git-on-the-Server-Generating-Your-SSH-Public-Key>`_ to generate a public key.

6. After completing these steps, check the email address provided above to verify it. It takes approximately 10-20 minutes for the website to become available.

7. Monitor the installation progress:

  * Launch a new `AWS Management Console <https://aws.amazon.com/console>`_ window, and use the top-level search bar to find and launch the AWS **CloudFormation** Service.
  * Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
  * Select **Stacks** from the left navigation menu.
  * Click an item (**WrfIntelImageBuilder**, **WrfCloudApiData**, or **WrfCloudWebApp**) listed in the **Stack name** column and select the **Events** tab to monitor progress.

8. When installation completes, a log message in the CloudShell terminal directs you to the newly created WRF Cloud URL.

  .. code-block:: ini

    WRF Cloud installation is complete.
    Open your browser to https://app.{DOMAIN}

9. Confirm that you can login.

  * Open a web browser and clear the cache to ensure a clean test environment.
  * Navigate to https://app.{DOMAIN}.
  * If directed to the **WRF Cloud Login** page, use the administrator email address and password defined above to login and proceed to the next step.
  * If, however, your browser downloads a file named **download** rather than allowing you to login, follow the steps outlined below to fix this behavior.

    a. In the CloudShell terminal, check that temporary build directory still exists. It should remain for a while after install but will eventually be scrubbed from **/tmp**.

    .. code-block:: ini

       ls /tmp/wrfcloud-build-*

    b. If it exists, run the following commands to update the WRF Cloud web files:

    .. code-block:: ini

      cd /tmp/wrfcloud-build-*
      bucket=`aws s3 ls | sed -r 's/ /\n/g' | grep wrfcloud`
      find web -type f -exec aws s3 cp {} s3://${bucket}/\{\} \;

    c. Create an AWS **CloudFront** invalidation.

      * Use the top-level search bar to find and launch the AWS **CloudFront** Service.
      * In **Distributions**, click on the **ID** for the line whose **Description** is **wrfcloud production**.
      * Select the **Invalidations** tab and click **Create Invalidation**.
      * In the **Add object paths** text box, type **/\***, and click **Create Invalidation**.

    d. In your browser window, clear your cache and navigate to https://app.{DOMAIN} again. If the **download** problem persists, repeats steps (a)-(c) until it stops. Remember to *clear your browser cache* before checking the URL.

10. Confirm that the WRF Amazon Machine Image (AMI) has finished building.

  * Use the top-level search bar to find and launch the AWS **EC2** Service.
  * Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
  * Select **Images > AMIs** from the left navigation menu and search for **wrf**.
  * Confirm that an AMI that includes **wrf** in the **AMI name** column.
  * Note that it may take several hours for this AMI to finish building. While you can add new users and configurations via the WRF Cloud user interface, you will not be able to actually launch a run until the WRF AMI is available.

11. After completing these installation steps, proceed to System Administration (:numref:`administration`).

.. _uninstall:

Procedures to Uninstall
=======================

The steps for uninstalling WRF Cloud from an AWS account are described below.

1. Login to the `AWS Management Console <https://aws.amazon.com/console>`_ for your account as a user with sufficient permissions (see :numref:`permissions`).

2. Remove data from S3.

  * Use the top-level search bar to find and launch the AWS **S3** Service.
  * Select **Buckets** from the left navigation menu and search for **wrfcloud**.
  * Select the **wrfcloud-XXXXXXX** S3 bucket and click **Empty** to remove its contents.

    * Do not **Delete** this bucket, as CloudFormation will handle that step.

3. Remove IAM policy.

  * Use the top-level search bar to find and launch the AWS **IAM** Service.
  * Select **Access Management > Policies** from the left navigation menu and search for **wrfcloud**.
  * Click the **wrfcloud_parallelcluster** radio button and select **Actions > Delete**.

    * Any other **wrfcloud** policies do not need to be removed.

4. Modify EC2 settings.

  * Use the top-level search bar to find and launch the AWS **EC2** Service.
  * Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
  * Remove the wrfcloud Amazon Machine Image (AMI).

    * Select **Images > AMIs** from the left navigation menu and search for **wrf**.
    * Make note of the **AMI ID** for the **wrf** AMI.
    * Select that AMI followed by **Actions > Deregister AMI**.

  * Remove any AMI Snapshots.

    * Select **Elastic Block Store > Snapshots** from the left navigation menu.
    * Select any entries for which the **AMI ID** noted above appears in the **Description** column.
    * Select **Actions > Delete snapshot** to remove them.

  * Remove the SSH key.

    * Select **Network & Security > Key Pairs** from the left navigation menu.
    * Select the **wrfcloud-admin** key pair followed by **Actions > Delete**.

5. Modify SES settings.

  * Use the top-level search bar to find and launch the AWS **SES** Service.
  * Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
  * Select **Configuration > Verified Identities** from the left navigation menu.
  * Select and **Delete** the email identity for your administrator's email address.

6. Delete CloudFormation stacks.

  * Use the top-level search bar to find and launch the AWS **CloudFormation** Service.
  * Select the **US East (Ohio) / us-east-2** region from the top-right dropdown navigation.
  * Select **Stacks** from the left navigation menu.
  * Select and **Delete** each of the following stacks: **WrfIntelImageBuilder**, **WrfCloudWebApp**
  * Wait for **WrfCloudWebApp** to be completely deleted.  If a delete fails, delete it again, and DO NOT retain the resources.
  * Select and **Delete** the following stack: **WrfCloudApiData**
  * Switch to the **US East (N. Virginia) / us-east-1** region and **Delete** the following stack: **WrfCloudWebCertificate**

You have now finished uninstalling WRF Cloud from your AWS account.
