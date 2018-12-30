from logzero import logger

from find_sale_in_wish_list import deserialize
from find_sale_in_wish_list.notification import SlackMessage
from find_sale_in_wish_list.amazon_wish_list import WishList
from find_sale_in_wish_list.headless_chrome import HeadlessChrome


def lambda_handler(event, context):
    """
    Trigger: dynamodb delete event
    monitor に対応した通知を送る
    :param event:
    :param context:
    :return:
    """

    recodes = event['Records']

    for recode in recodes:
        if not recode['eventName'] == 'REMOVE':
            continue
        headless_chrome = HeadlessChrome()
        queue_item = deserialize(recode['dynamodb']['OldImage'])
        logger.info("queue_item　%s", queue_item)
        kindle_books_dict = get_kindle_books(queue_item, headless_chrome)
        notify(queue_item, kindle_books_dict)
        headless_chrome.driver.close()

    logger.info('finish:notification')


def get_kindle_books(queue_item: dict, headless_chrome: HeadlessChrome) -> dict:
    wish_list_url = queue_item['wish_list_url']
    wish_list = WishList(url=wish_list_url, headless_chrome=headless_chrome)
    book_url_list = wish_list.get_kindle_book_url_list()
    kindle_books_dict = wish_list.get_kindle_books(book_url_list)
    return kindle_books_dict


def notify(queue_item: dict, kindle_books_dict: dict) -> None:
    threshold = queue_item['threshold']
    point_threshold = threshold.get('points', 0)
    discount_threshold = threshold.get('discount_rate', 0)

    notification = queue_item['notification']
    logger.info("notification　%s", notification)
    slack_incoming_web_hook = notification['incoming_web_hook']
    slack_channel = notification['slack_channel']

    slack_message = SlackMessage(slack_incoming_web_hook=slack_incoming_web_hook,
                                 slack_channel=slack_channel)
    slack_message.add_high_discount_rate_books(kindle_books_dict, discount_threshold)
    slack_message.add_high_loyalty_points_books(kindle_books_dict, point_threshold)
    slack_message.post()
    logger.info("finish:post")
