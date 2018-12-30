from logzero import logger
import os
import boto3
import calendar
import time


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
    queue_monitors = dynamodb.Table(os.environ['QUEUE_MONITORS'])
    users = table_users.scan().get("Items")

    for user in users:
        logger.info("user: %s", user)
        user_id = user['user_id']
        monitors = user['monitors']
        for monitor in monitors:
            monitor['user_id'] = user_id
            monitor["expired"] = calendar.timegm(time.gmtime()) + (3 * 60)
            queue_monitors.put_item(Item=monitor)
            logger.info("monitor: %s", monitor)

