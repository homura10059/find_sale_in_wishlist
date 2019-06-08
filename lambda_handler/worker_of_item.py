from logzero import logger

from find_sale_in_wish_list.notification import SlackMessage
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

    notify(event, res)


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
