import calendar
import os
import time

import boto3
from logzero import logger

from find_sale_in_wish_list import deserialize
from find_sale_in_wish_list.amazon_wish_list import KindleBook
from find_sale_in_wish_list.headless_chrome import HeadlessChrome


def lambda_handler(event, context):
    """
     Trigger: dynamodb insert event
     monitor から item を抜き出し enqueue する
     :param event:
     :param context:
     :return:
     """
    recodes = event['Records']

    response_list = []
    for recode in recodes:
        if not recode['eventName'] == 'INSERT':
            continue
        headless_chrome = HeadlessChrome()
        image = deserialize(recode['dynamodb']['NewImage'])
        logger.info("queue_item　%s", image)
        kindle_book = KindleBook(headless_chrome)
        res = kindle_book.get(url=image["item_url"])
        response_list.append(res)
        headless_chrome.driver.close()

    return response_list

