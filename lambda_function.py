import requests
import os
from logzero import logger
import logzero
import json
from scraping.amazon_wish_list import WishList
from scraping.headless_chrome import HeadlessChrome

formatter = logzero.LogFormatter(
    fmt="%(asctime)s|%(filename)s:%(lineno)d|%(levelname)-7s : %(message)s",
)
logzero.formatter(formatter)


def build_attachments(kindle_books_list, point_threshold=20, discount_threshold=20):
    color = "good"

    attachments = []

    over_points_list = list(filter(lambda x: x[1]['loyalty_points'] >= point_threshold, kindle_books_list.items()))
    for kindle_id, kindle_book in over_points_list:
        text = "{} % ポイント還元".format(kindle_book['loyalty_points'])
        attachment = {
            "text": text,
            "color": color,
            "title": kindle_book['book_title'],
            "title_link": kindle_book['url'],
        }
        attachments.append(attachment)

    discount_list = list(filter(lambda x: x[1]['discount_rate'] >= discount_threshold, kindle_books_list.items()))
    for kindle_id, kindle_book in discount_list:
        text = "{} % 割引".format(kindle_book['discount_rate'])
        attachment = {
            "text": text,
            "color": color,
            "title": kindle_book['book_title'],
            "title_link": kindle_book['url'],
        }
        attachments.append(attachment)

    return attachments


def build_slack_message(channel, kindle_books_list):
    attachments = build_attachments(kindle_books_list)
    # SlackにPOSTする内容をセット
    slack_message = {
        'channel': channel,
        "attachments": attachments,
    }
    return slack_message


def lambda_handler(event, context):
    wish_list_url = event['wish_list_url']
    slack_incoming_web_hook = event['slack_incoming_web_hook']
    slack_channel = event['slack_channel']

    headless_chrome = HeadlessChrome()
    wish_list = WishList(url=wish_list_url, headless_chrome=headless_chrome)
    book_url_list = wish_list.get_kindle_book_url_list()
    kindle_books_list = wish_list.get_kindle_books(book_url_list)

    headless_chrome.driver.close()

    slack_message = build_slack_message(slack_channel, kindle_books_list)
    # SlackにPOST
    try:
        req = requests.post(slack_incoming_web_hook, data=json.dumps(slack_message))
        logger.info("Message posted to %s", slack_message['channel'])
    except requests.exceptions.RequestException as e:
        logger.error("Request failed: %s", e)


if __name__ == "__main__":
    lambda_event = {
        # 'wish_list_url': "http://amzn.asia/g3GNM5i",
        'wish_list_url': "http://amzn.asia/4JzxGVQ",
        'slack_incoming_web_hook': os.environ['slackPostURL'],
        'slack_channel': os.environ['slackChannel'],
    }

    lambda_handler(lambda_event, None)
