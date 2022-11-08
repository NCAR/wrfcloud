#! /bin/bash

mkdir -p /data/__REF_ID__
cd /data/__REF_ID__
echo -n "__CONFIG_B64_GZ__" | base64 -d | gunzip > run.yml

aws s3 sync s3://wrfcloud-xfer-tmp/ .
mkdir -p configurations/__CONFIG_NAME__
mv geo_em.d01.nc configurations/__CONFIG_NAME__
cp namelist.wps configurations/__CONFIG_NAME__
cp namelist.input configurations/__CONFIG_NAME__
chown -R ec2-user.ec2-user /data/__REF_ID__
unset I_MPI_OFI_PROVIDER
su ec2-user -c /opt/python/bin/wrfcloud-run > wrfcloud-run.log 2>&1 &
