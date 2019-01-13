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

    headless_chrome = HeadlessChrome()
    kindle_book = KindleBook(headless_chrome)
    url = event["item_url"]
    book = kindle_book.get(url=url)
    res = {url: book}
    headless_chrome.driver.close()
    logger.info("res: %s",  res)
    return res

