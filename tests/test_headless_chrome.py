import json

from lambda_function import kindle_books_get
from scraping.headless_chrome import HeadlessChrome


def test_init():
    hc = HeadlessChrome()
    hc.driver.close()


def test_kindle_books_get():
    lambda_event = {
        'queryStringParameters': {
            "wishListUrl": "http%3A%2F%2Famzn.asia%2F4JzxGVQ"
        }
    }

    res = kindle_books_get(lambda_event, None)
    print(res)
