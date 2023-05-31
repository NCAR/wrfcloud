#! /bin/bash

source /etc/bashrc
export WRFCLOUD_BUCKET="__S3_BUCKET__"
export APP_HOSTNAME="__APP_HOSTNAME__"
export API_HOSTNAME="__API_HOSTNAME__"
export JWT="__JWT__"
su ec2-user -c "mkdir -p /data/__JOB_ID__"
su ec2-user -c "/opt/python/bin/wrfcloud-run --job-id __JOB_ID__" > /data/__JOB_ID__/wrfcloud-run-__JOB_ID__.log 2>&1 &
