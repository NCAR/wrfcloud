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
* Domain name in Route 53 (optional)

Procedures for initial installation
===================================

From the AWS web console, switch the region to us-east-2 (Ohio), then click on the CloudShell icon at the top of the screen to start CloudShell.

From CloudShell:


* git clone https://github.com/NCAR/wrfcloud
* ./wrfcloud/install_bootstrap.sh


Procedures to uninstall the application
=======================================

* Remove data from S3 bucket named wrfcloud-XXXXXXX
* Remove the wrfcloud_parallelcluster IAM policy
* Remove the AMI from the EC2 service (be sure to deregister the AMI and delete the snapshots!)
* Remove the SSH key from the EC2 service named wrfcloud-admin
* Remove the SES email identity for your admin's email address
* Delete CloudFormation stacks: WrfIntelImageBuilder, WrfCloudWebApp, WrfCloudApiData, WrfCloudWebCertificate (us-east-1)
