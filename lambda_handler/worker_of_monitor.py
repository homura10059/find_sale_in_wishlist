import calendar
import os
import time

import boto3
from logzero import logger

from find_sale_in_wish_list import deserialize
from find_sale_in_wish_list.amazon_wish_list import WishList
from find_sale_in_wish_list.headless_chrome import HeadlessChrome


def lambda_handler(event, context):
    """
     Trigger: dynamodb insert event
     monitor から item を抜き出し enqueue する
     :param event:
     :param context:
     :return:
     """
    dynamodb = boto3.resource('dynamodb')
    queue_items = dynamodb.Table(os.environ['QUEUE_ITEMS'])

    recodes = event['Records']

    for recode in recodes:
        if not recode['eventName'] == 'INSERT':
            continue
        headless_chrome = HeadlessChrome()
        image = deserialize(recode['dynamodb']['NewImage'])
        logger.info("queue_item　%s", image)
        enqueue_item(headless_chrome, image, queue_items)
        headless_chrome.driver.close()


def enqueue_item(headless_chrome, image, queue_items):
    wish_list_url = image['wish_list_url']
    wish_list = WishList(url=wish_list_url, headless_chrome=headless_chrome)
    book_url_list = wish_list.get_kindle_book_url_list()
    for url in book_url_list:
        record = {
            "item_url": url,
            "expired": calendar.timegm(time.gmtime()) + (3 * 60)
        }
        queue_items.put_item(Item=record)
        logger.info("item_queue: %s", record)
