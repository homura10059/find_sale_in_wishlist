from concurrent.futures import ThreadPoolExecutor

from logzero import logger

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
    on_event(event)


def on_event(queue_item: dict)-> None:
    headless_chrome = HeadlessChrome()
    wish_list_url = queue_item['wish_list_url']
    wish_list = WishList(url=wish_list_url, headless_chrome=headless_chrome)
    book_url_list = wish_list.get_kindle_book_url_list()

    with ThreadPoolExecutor(thread_name_prefix="thread") as executor:
        futures = []
        for book_url in book_url_list:
            futures.append(executor.submit(invoke_lambda, book_url, queue_item))
        logger.info("submit end")
        logger.info([f.result() for f in futures])

    headless_chrome.driver.close()


def invoke_lambda(url: str, queue_item: dict)-> list:
    client_lambda = boto3.client("lambda")
    function_name = os.environ['WORKER_ITEM']
    params = {
        "item_url": url,
        "threshold": queue_item['threshold'],
        "notification": queue_item['notification']
    }
    payload = json.dumps(params)

    logger.info("function_name %s", function_name)
    client_lambda.invoke(
        FunctionName=function_name,
        InvocationType="Event",
        Payload=payload
    )

    return payload

