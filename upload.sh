#!/usr/bin/env bash

docker run --rm -v "${PWD}":/var/task lambda_headless_chrome
aws s3 cp deploy_package.zip s3://lambda-fanction
#aws lambda create-function \
#    --region ap-northeast-1 \
#    --function-name lambda_headless_chrome_python \
#    --runtime python3.6 \
#    --role arn:aws:iam::267428311438:role/AWSLambdaFullAccess \
#    --code S3Bucket=lambda-fanction,S3Key=deploy_package.zip \
#    --handler lambda_function.lambda_handler \
#    --memory-size 512 --timeout 300
aws lambda update-function-code \
    --region ap-northeast-1 \
    --function-name lambda_headless_chrome_python \
    --s3-bucket=lambda-fanction \
    --s3-key=deploy_package.zip