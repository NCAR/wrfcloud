#! /bin/bash

source /etc/bashrc
unset I_MPI_OFI_PROVIDER
export WRFCLOUD_BUCKET="__S3_BUCKET__"
su ec2-user -c /opt/python/bin/wrfcloud-run --job-id __JOB_ID__ > wrfcloud-run.log 2>&1 &
