import json
from concurrent.futures import ThreadPoolExecutor

from logzero import logger
import os
import boto3
import calendar
import time

from find_sale_in_wish_list import decimal_default


def lambda_handler(event, context):
    """
    Trigger: cloudwatch events
    System 全体のユーザー情報を取得して monitor を enqueue する
    :param event:
    :param context:
    :return:
    """
    dynamodb = boto3.resource('dynamodb')
    table_users = dynamodb.Table(os.environ['TABLE_USER'])
    users = table_users.scan().get("Items")

    for user in users:
        logger.info("user: %s", user)
        user_id = user['user_id']
        monitors = user['monitors']
        with ThreadPoolExecutor(thread_name_prefix="thread") as executor:
            futures = []
            for monitor in monitors:
                monitor['user_id'] = user_id
                monitor["expired"] = calendar.timegm(time.gmtime()) + 60
                futures.append(executor.submit(invoke_lambda, monitor))
            logger.info("submit end")
            logger.info([f.result() for f in futures])


def invoke_lambda(monitor: dict)-> None:
    client_lambda = boto3.client("lambda")
    payload = json.dumps(monitor, default=decimal_default)
    logger.info("start %s", payload)
    function_name = os.environ['NOTIFIER']
    logger.info("function_name %s", function_name)
    client_lambda.invoke(
        FunctionName=function_name,
        InvocationType="Event",
        Payload=payload
    )
    return payload
