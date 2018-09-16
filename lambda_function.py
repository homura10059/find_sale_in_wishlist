import requests
import os
from logzero import logger
import logzero
import json
from scraping.amazon_wish_list import WishList, KindleBook
from scraping.headless_chrome import HeadlessChrome

formatter = logzero.LogFormatter(
    fmt="%(asctime)s|%(filename)s:%(lineno)d|%(levelname)-7s : %(message)s",
)
logzero.formatter(formatter)


class SlackMessage:
    color = "good"

    def __init__(self, slack_incoming_web_hook, slack_channel):
        self.slack_incoming_web_hook = slack_incoming_web_hook
        self.slack_channel = slack_channel
        self.attachments = []

    def add_high_loyalty_points_books(self, kindle_books_list, point_threshold=20):

        attachments = []

        over_points_list = list(filter(lambda x: x[1]['loyalty_points'] >= point_threshold, kindle_books_list.items()))
        for kindle_id, kindle_book in over_points_list:
            text = "{} % ポイント還元".format(kindle_book['loyalty_points'])
            attachment = {
                "text": text,
                "color": self.color,
                "title": kindle_book['book_title'],
                "title_link": kindle_book['url'],
            }
            attachments.append(attachment)

        self.attachments.extend(attachments)

    def add_high_discount_rate_books(self, kindle_books_list, discount_threshold=20):

        attachments = []
        discount_list = list(filter(lambda x: x[1]['discount_rate'] >= discount_threshold, kindle_books_list.items()))
        for kindle_id, kindle_book in discount_list:
            text = "{} % 割引".format(kindle_book['discount_rate'])
            attachment = {
                "text": text,
                "color": self.color,
                "title": kindle_book['book_title'],
                "title_link": kindle_book['url'],
            }
            attachments.append(attachment)

        self.attachments.extend(attachments)

    def build_data(self):
        # SlackにPOSTする内容をセット
        slack_message = {
            'channel': self.slack_channel,
            "attachments": self.attachments,
        }
        return json.dumps(slack_message)

    def post(self):
        # SlackにPOST
        try:
            req = requests.post(self.slack_incoming_web_hook, data=self.build_data())
            logger.info("Message posted to %s", self.slack_channel)
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", e)


def get_kindle_books(wish_list_url: str) -> dict:
    headless_chrome = HeadlessChrome()
    wish_list = WishList(url=wish_list_url, headless_chrome=headless_chrome)
    book_url_list = wish_list.get_kindle_book_url_list()
    kindle_books_list = wish_list.get_kindle_books(book_url_list)
    headless_chrome.driver.close()
    return kindle_books_list


def lambda_handler(event, context):
    wish_list_url = event['wish_list_url']
    slack_incoming_web_hook = event['slack_incoming_web_hook']
    slack_channel = event['slack_channel']
    point_threshold = event.get('point_threshold', 20)
    discount_threshold = event.get('discount_threshold', 20)

    kindle_books_dict = get_kindle_books(wish_list_url=wish_list_url)

    slack_message = SlackMessage(slack_incoming_web_hook=slack_incoming_web_hook,
                                 slack_channel=slack_channel)
    slack_message.add_high_discount_rate_books(kindle_books_dict, discount_threshold)
    slack_message.add_high_loyalty_points_books(kindle_books_dict, point_threshold)
    slack_message.post()


def handler_worker_scraping(event, context):
    headless_chrome = HeadlessChrome()
    kindle_book = KindleBook(headless_chrome)
    kindle_books = []
    for record in event['Records']:
        kindle_book_url = record['body']
        logger.info("JSON body: %s", kindle_book_url)
        book_dict = kindle_book.get(url=kindle_book_url)
        kindle_books.append(book_dict)
    headless_chrome.driver.close()
    logger.info("kindle_books: %s", kindle_books)
    return kindle_books


if __name__ == "__main__":
    lambda_event = {
        # 'wish_list_url': "http://amzn.asia/g3GNM5i",
        'wish_list_url': "http://amzn.asia/4JzxGVQ",
        'slack_incoming_web_hook': os.environ['slackPostURL'],
        'slack_channel': os.environ['slackChannel'],
        'point_threshold': 30,
        'discount_threshold': 30
    }

    lambda_handler(lambda_event, None)
