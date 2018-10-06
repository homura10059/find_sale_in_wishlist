import requests
import os

from boto3.dynamodb.conditions import Key
from logzero import logger
import logzero
import json
from scraping.amazon_wish_list import WishList, KindleBook
from scraping.headless_chrome import HeadlessChrome
import boto3
from string import Template
import textwrap
import locale

locale.setlocale(locale.LC_ALL, '')

formatter = logzero.LogFormatter(
    fmt="%(asctime)s|%(filename)s:%(lineno)d|%(levelname)-7s : %(message)s",
)
logzero.formatter(formatter)


class SlackMessage:
    color = "good"

    def __init__(self, slack_incoming_web_hook, slack_channel):
        self.slack_incoming_web_hook = slack_incoming_web_hook
        self.slack_channel = slack_channel
        self.books = {}

    def add_high_loyalty_points_books(self, kindle_books_list, point_threshold=20):
        over_points_dict = dict(filter(lambda x: x[1]['loyalty_points'] >= point_threshold, kindle_books_list.items()))
        self.books = {**self.books, **over_points_dict}

    def add_high_discount_rate_books(self, kindle_books_list, discount_threshold=20):
        discount_dict = dict(filter(lambda x: x[1]['discount_rate'] >= discount_threshold, kindle_books_list.items()))
        self.books = {**self.books, **discount_dict}

    def build_data(self):

        attachments = []

        locale.setlocale(locale.LC_ALL, ('ja_JP', 'UTF-8'))

        for kindle_id, kindle_book in self.books.items():
            kindle_book['price'] = locale.currency(kindle_book['price'], grouping=True)

            text_template = """
            金額: ${price}
            値引き率: ${discount_rate}%
            ポイント還元率: ${loyalty_points}%
            """
            temp = Template(textwrap.dedent(text_template))
            text = temp.safe_substitute(kindle_book)

            attachment = {
                "text": text,
                "color": self.color,
                "title": kindle_book['book_title'],
                "title_link": kindle_book['url'],
            }
            attachments.append(attachment)

        # SlackにPOSTする内容をセット
        slack_message = {
            'channel': self.slack_channel,
            "attachments": attachments,
        }
        return json.dumps(slack_message)

    def post(self):
        # SlackにPOST
        try:
            req = requests.post(self.slack_incoming_web_hook, data=self.build_data())
            logger.info("Message posted to %s", self.slack_channel)
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", e)


def __get_kindle_books(wish_list_url: str) -> dict:
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

    kindle_books_dict = __get_kindle_books(wish_list_url=wish_list_url)

    slack_message = SlackMessage(slack_incoming_web_hook=slack_incoming_web_hook,
                                 slack_channel=slack_channel)
    slack_message.add_high_discount_rate_books(kindle_books_dict, discount_threshold)
    slack_message.add_high_loyalty_points_books(kindle_books_dict, point_threshold)
    slack_message.post()


def worker_scraping_wish_list(event, context):

    # sqs への通信でエラーになった時余計な処理をしないために最初に取得する
    sqs = boto3.client('sqs')
    queue = sqs.get_queue_url(QueueName="worker_scraping_book")
    logger.debug("sqs queue: %s", queue)

    url_in_wish_list = []

    headless_chrome = HeadlessChrome()
    for record in event['Records']:
        body = json.loads(record['body'])
        logger.info("JSON body: %s", body)
        wish_list_url = body['url']
        logger.info("wish_list_url: %s", wish_list_url)
        wish_list = WishList(url=wish_list_url, headless_chrome=headless_chrome)
        book_url_list = wish_list.get_kindle_book_url_list()
        url_in_wish_list.extend(book_url_list)
    headless_chrome.driver.close()

    unique_url_list = list(set(url_in_wish_list))

    for url in unique_url_list:
        # SQSへJSONの送信
        body = {"url": url}
        response = sqs.send_message(
            QueueUrl=queue['QueueUrl'],
            DelaySeconds=0,
            MessageBody=(
                json.dumps(body)
            )
        )
        logger.info("sqs response: %s", response)

    logger.info("url_in_wish_list: %s", unique_url_list)
    return unique_url_list


def worker_scraping_book(event, context):
    headless_chrome = HeadlessChrome()
    kindle_book = KindleBook(headless_chrome=headless_chrome)
    kindle_books = []
    for record in event['Records']:
        body = json.loads(record['body'])
        logger.info("JSON body: %s", body)
        kindle_book_url = body['url']
        book_dict = kindle_book.get(url=kindle_book_url)
        kindle_books.append(book_dict)
    headless_chrome.driver.close()
    logger.info("kindle_books: %s", kindle_books)
    return kindle_books


def worker_user(event, context):

    # 依存リソース への通信でエラーになった時余計な処理をしないために最初に取得する
    table = __get_dynamo_db_table('kindle_sale_wish_list')
    sqs = boto3.client('sqs')
    queue = sqs.get_queue_url(QueueName="worker_scraping_wish_list")
    logger.debug("sqs queue: %s", queue)

    wish_list_url_list = []
    for record in event['Records']:
        body = json.loads(record['body'])
        logger.info("JSON body: %s", body)
        user_id = int(body['user_id'])
        logger.info("user_id: %s", user_id)

        result = table.query(
            IndexName='user_id-index',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )

        for item in result.get("Items"):
            wish_list_url_list.append(item.get('url'))

    unique_url_list = list(set(wish_list_url_list))

    for url in unique_url_list:
        # SQSへJSONの送信
        body = {"url": url}
        response = sqs.send_message(
            QueueUrl=queue['QueueUrl'],
            DelaySeconds=0,
            MessageBody=(
                json.dumps(body)
            )
        )
        logger.info("sqs response: %s", response)

    logger.info("wish_list_url_list: %s", unique_url_list)
    return unique_url_list


def __get_dynamo_db_table(name):
    endpoint_url = os.environ.get("dynamo_endpoint_url")

    if endpoint_url is None:
        dynamo_db = boto3.resource('dynamodb')
    else:
        dynamo_db = boto3.resource('dynamodb', endpoint_url=endpoint_url)

    table = dynamo_db.Table(name)
    logger.debug("table: %s", table)

    return table


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
