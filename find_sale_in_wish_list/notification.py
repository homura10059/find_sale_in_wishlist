import json
import locale
import textwrap
from decimal import Decimal
from string import Template

import requests
from logzero import logger


class SlackMessage:
    color = "good"

    def __init__(self, slack_incoming_web_hook, slack_channel):
        self.slack_incoming_web_hook = slack_incoming_web_hook
        self.slack_channel = slack_channel
        self.books = {}

    def add_high_loyalty_points_books(self, kindle_books_dict: dict, point_threshold=20):
        over_points_dict = {}
        for key, value in kindle_books_dict.items():
            if value['loyalty_points'] > Decimal(point_threshold):
                over_points_dict[key] = value
        self.books = {**self.books, **over_points_dict}

    def add_high_discount_rate_books(self, kindle_books_dict, discount_threshold=20):
        discount_dict = {}
        for key, value in kindle_books_dict.items():
            if value['discount_rate'] > Decimal(discount_threshold):
                discount_dict[key] = value
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