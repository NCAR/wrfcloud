.. _installation:

*******************
System Installation
*******************

Introduction
============

The WRF Cloud framework can be installed in any AWS account via CloudShell.

Prerequisites
=============

* AWS Account
* Domain name in Route 53

Procedures for initial installation
===================================

From the AWS web console, switch the region to us-east-2 (Ohio), then click on the CloudShell icon at the top of the screen to start CloudShell.

From CloudShell:

* git clone --branch feature/auto-install https://github.com/NCAR/wrfcloud
* ./wrfcloud/install_bootstrap.sh
[The bootstrap takes about 25 minutes to complete and is followed by some questions before WRF Cloud is installed in your account.]

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
