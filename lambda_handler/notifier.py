from concurrent.futures import ThreadPoolExecutor

from logzero import logger

from find_sale_in_wish_list.notification import SlackMessage
from find_sale_in_wish_list.amazon_wish_list import WishList
from find_sale_in_wish_list.headless_chrome import HeadlessChrome
import os
import boto3
import json


def lambda_handler(event, context):
    """
    monitor に対応した通知を送る
    :param event:
    :param context:
    :return:
    """
    logger.info("event: %s", event)
    on_insert_event(event)


def on_insert_event(queue_item: dict):
    headless_chrome = HeadlessChrome()
    wish_list_url = queue_item['wish_list_url']
    wish_list = WishList(url=wish_list_url, headless_chrome=headless_chrome)
    book_url_list = wish_list.get_kindle_book_url_list()
    with ThreadPoolExecutor(thread_name_prefix="thread") as executor:
        results = executor.map(invoke_lambda, book_url_list)
        logger.info("invoke worker_of_item and waiting result...")
    listed_result = list(results)
    logger.info("listed_result: %s",  listed_result)

    result_dict = {}
    for result in listed_result:
        result_dict.update(result)
    notify(queue_item, result_dict)

    headless_chrome.driver.close()


def invoke_lambda(url: str)-> list:
    client_lambda = boto3.client("lambda")
    params = {
        "item_url": url,
    }
    res = client_lambda.invoke(
        FunctionName=os.environ['WORKER_ITEM'],
        InvocationType="RequestResponse",
        Payload=json.dumps(params)
    )
    payload = json.loads(res['Payload'].read())

    return payload


def get_kindle_books(queue_item: dict, headless_chrome: HeadlessChrome) -> dict:
    wish_list_url = queue_item['wish_list_url']
    wish_list = WishList(url=wish_list_url, headless_chrome=headless_chrome)
    book_url_list = wish_list.get_kindle_book_url_list()
    kindle_books_dict = wish_list.get_kindle_books(book_url_list)
    return kindle_books_dict


def notify(queue_item: dict, kindle_books_dict_list: dict) -> None:
    threshold = queue_item['threshold']
    point_threshold = threshold.get('points', 0)
    discount_threshold = threshold.get('discount_rate', 0)

    notification = queue_item['notification']
    logger.info("notification %s", notification)
    slack_incoming_web_hook = notification['incoming_web_hook']
    slack_channel = notification['slack_channel']

    slack_message = SlackMessage(slack_incoming_web_hook=slack_incoming_web_hook,
                                 slack_channel=slack_channel)
    slack_message.add_high_discount_rate_books(kindle_books_dict_list, discount_threshold)
    slack_message.add_high_loyalty_points_books(kindle_books_dict_list, point_threshold)
    slack_message.post()
    logger.info("finish:post")
