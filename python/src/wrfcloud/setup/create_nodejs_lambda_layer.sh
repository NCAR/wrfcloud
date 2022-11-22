#! /bin/bash

# download and install Node 16 with the Node Version Manager (nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash
chmod ug+x ~/.nvm/nvm.sh
source ~/.nvm/nvm.sh
nvm install 16

# move the installation to /opt/node
mkdir /opt/node
mv ~/.nvm/versions/node/v16.18.1/* /opt/node

# create a zip file from the node package
cd /opt/
zip -r node-16.18.1.tar.gz node

# copy the zip file to S3 and publish the lambda layer
aws s3 cp node-16.18.1.tar.gz s3://__BUCKET__/node-16.18.1.tar.gz
# Next line not tested
# aws lambda publish-lambda-layer --layer-name node16 --compatible-runtimes python3.9 --content S3Bucket=__BUCKET__,S3Key=node-16.18.1.tar.gz