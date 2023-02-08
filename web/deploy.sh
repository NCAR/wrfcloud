#! /bin/bash

profile="wrfcloud"
region="us-east-2"
distribution_id="E1TD694S70U8ZW"
bucket="wrfcloud-afdd9908"

rm -Rf dist/
ng build
cd dist/web/
aws --profile ${profile} --region ${region} \
    s3 sync . s3://${bucket}/web/
invalidation_id=$(aws --profile ${profile} --region ${region} cloudfront create-invalidation --distribution-id ${distribution_id} --paths '/*' | jq -r .Invalidation.Id)
for i in $(seq 1 20); do
    aws --profile ${profile} --region ${region} \
        cloudfront get-invalidation \
            --distribution-id ${distribution_id} \
            --id ${invalidation_id} | jq -r .Invalidation.Status
    sleep 2
done
echo "aws --profile ${profile} --region ${region} cloudfront get-invalidation --distribution-id ${distribution_id} --id ${invalidation_id} | jq -r .Invalidation.Status"
