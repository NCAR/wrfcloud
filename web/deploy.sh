#! /bin/bash

profile="wrfcloud"
region="us-east-2"
distribution_id="E1X9K3GKJ3DMF6"
bucket="www.wrfcloud.com"

rm -Rf dist/
ng build
cd dist/web/
aws --profile ${profile} --region ${region} \
    s3 sync . s3://${bucket}/
invalidation_id=$(aws --profile ${profile} --region ${region} cloudfront create-invalidation --distribution-id ${distribution_id} --paths '/*' | jq -r .Invalidation.Id)
for i in $(seq 1 20); do
    aws --profile ${profile} --region ${region} \
        cloudfront get-invalidation \
            --distribution-id ${distribution_id} \
            --id ${invalidation_id} | jq -r .Invalidation.Status
    sleep 2
done
echo "aws --profile ${profile} --region ${region} cloudfront get-invalidation --distribution-id ${distribution_id} --id ${invalidation_id} | jq -r .Invalidation.Status"
