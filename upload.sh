#!/usr/bin/env bash

docker run --rm -v "${PWD}":/var/task lambda_headless_chrome
aws s3 cp deploy_package.zip s3://lambda-fanction


#aws lambda create-function \
#    --region ap-northeast-1 \
#    --function-name worker_scraping \
#    --runtime python3.6 \
#    --role arn:aws:iam::267428311438:role/lambda-queue \
#    --code S3Bucket=lambda-fanction,S3Key=deploy_package.zip \
#    --handler lambda_function.lambda_handler \
#    --memory-size 256 --timeout 300 \
#    --dead-letter-config TargetArn=arn:aws:sns:ap-northeast-1:267428311438:failed-lambda \
#    --tags service=knedle_sale

#aws sqs create-queue \
#    --queue-name worker_scraping_book \
#    --attributes VisibilityTimeout=300
#
#aws lambda create-function \
#    --region ap-northeast-1 \
#    --function-name worker_scraping_book \
#    --runtime python3.6 \
#    --role arn:aws:iam::267428311438:role/lambda-queue \
#    --code S3Bucket=lambda-fanction,S3Key=deploy_package.zip \
#    --handler lambda_function.worker_scraping_book \
#    --memory-size 256 --timeout 300 \
#    --dead-letter-config TargetArn=arn:aws:sns:ap-northeast-1:267428311438:failed-lambda \
#    --tags service=knedle_sale
#
#aws sqs create-queue \
#    --queue-name worker_scraping_wish_list \
#    --attributes VisibilityTimeout=300
#
#aws lambda create-function \
#    --region ap-northeast-1 \
#    --function-name worker_scraping_wish_list \
#    --runtime python3.6 \
#    --role arn:aws:iam::267428311438:role/lambda-queue \
#    --code S3Bucket=lambda-fanction,S3Key=deploy_package.zip \
#    --handler lambda_function.worker_scraping_wish_list \
#    --memory-size 256 --timeout 300 \
#    --dead-letter-config TargetArn=arn:aws:sns:ap-northeast-1:267428311438:failed-lambda \
#    --tags service=knedle_sale

#aws lambda update-function-code \
#    --region ap-northeast-1 \
#    --function-name lambda_headless_chrome_python \
#    --s3-bucket=lambda-fanction \
#    --s3-key=deploy_package.zip

aws lambda update-function-code \
    --region ap-northeast-1 \
    --function-name worker_scraping_book \
    --s3-bucket=lambda-fanction \
    --s3-key=deploy_package.zip

aws lambda update-function-code \
    --region ap-northeast-1 \
    --function-name worker_scraping_wish_list \
    --s3-bucket=lambda-fanction \
    --s3-key=deploy_package.zip