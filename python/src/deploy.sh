#! /bin/bash

# remove the old zip file
rm -f production_wrfcloud_handler.zip

# create a new zip file with current code
zip -r production_wrfcloud_handler.zip lambda_wrapper.py wrfcloud

# update the function code in aws
aws --profile wrfcloud --region us-east-2 \
    lambda update-function-code \
        --function-name production_wrfcloud_handler \
        --zip-file fileb://./production_wrfcloud_handler.zip

# delete the temporary zip file
rm -f production_wrfcloud_handler.zip
