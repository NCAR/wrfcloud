#! /bin/bash

source /etc/bashrc
unset I_MPI_OFI_PROVIDER
export WRFCLOUD_BUCKET="__S3_BUCKET__"
export APP_HOSTNAME="__APP_HOSTNAME__"
su ec2-user -c "/opt/python/bin/wrfcloud-run --job-id __JOB_ID__" > /data/wrfcloud-run-__JOB_ID__.log 2>&1 &
