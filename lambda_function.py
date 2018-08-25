from selenium import webdriver
import requests
import os
import platform
from logzero import logger
import logzero
import json
from bs4 import BeautifulSoup
from time import sleep
import re
from memorize.cache import cached

formatter = logzero.LogFormatter(
    fmt="%(asctime)s|%(filename)s:%(lineno)d|%(levelname)-7s : %(message)s",
)
logzero.formatter(formatter)


def get_web_driver():
    """
    headless-chrome の web-driver を生成
    :return: web-driver
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--disable-application-cache")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-sandbox")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--enable-logging")
    options.add_argument("--log-level=0")
    options.add_argument("--v=99")
    options.add_argument("--single-process")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--homedir=/tmp")

    if platform.system() == 'Darwin':
        file_path = '/usr/local/bin/chromedriver'
    else:
        options.binary_location = "./bin/headless-chromium"
        this_file_path = os.path.dirname(os.path.abspath(__name__))
        joined_path = os.path.join(this_file_path, './bin/chromedriver')
        file_path = os.path.normpath(joined_path).replace('/', os.sep)

    logger.debug("file_path: %s", file_path)
    driver = webdriver.Chrome(file_path, chrome_options=options)
    return driver


def get_full_page_html(driver, url):
    driver.get(url)

    # ページ最下部までスクロール
    pause_time = 1
    scroll_height = 1280

    while True:

        # スクロール
        driver.execute_script("window.scrollTo(0, {});".format(scroll_height))
        # 読み込み待ち
        sleep(pause_time)

        # HTMLを文字コードをUTF-8に変換してから取得
        html = driver.page_source.encode('utf-8')

        # 読み込みが完了したか確認
        selector = "#endOfListMarker > div > h5"
        soup = BeautifulSoup(html, "html.parser")
        list_end = soup.select_one(selector)
        if list_end is not None:
            break
        logger.debug("scroll_height:%s, pause_time:%s, url:%s", scroll_height, pause_time, url)
        # 読み込み時間を延長
        pause_time *= 2
        # スクロール距離を延長
        scroll_height *= 2

    logger.debug("complete get_full_page_html url:%s", url)

    html = driver.page_source.encode('utf-8')
    return html


@cached(timeout=60*60)
def get_href_list(driver, url):
    html = get_full_page_html(driver, url)
    soup = BeautifulSoup(html, "html.parser")

    href_list = []
    for link in soup.findAll("a"):
        if link.get("href") is not None \
                and "?coliid" in link.get('href') \
                and "&ref" in link.get('href'):
            href_list.append(link.get('href'))

    return href_list


def get_soup(driver, url):
    driver.get(url)
    html = driver.page_source.encode('utf-8')
    soup = BeautifulSoup(html, "html.parser")
    return soup


def get_book_title(soup):
    selector = "#ebooksProductTitle"
    book_title = soup.select_one(selector)
    return book_title.text


def get_discount_rate(soup):
    selector = "#buybox > div > table > tbody > tr.kindle-price > td.a-color-price.a-size-medium.a-align-bottom > p"
    kindle_price = soup.select_one(selector)
    discount_rate = 0
    regex = r"[0-9]*%"
    if kindle_price is not None:
        matches = re.search(regex, kindle_price.text)
        discount_rate = int(matches.group().split('%')[0])
    return discount_rate


def get_loyalty_points(soup):
    selector = "#buybox > div > table > tbody > tr.loyalty-points > td.a-align-bottom"
    point = soup.select_one(selector)
    loyalty_points = 0
    regex = r"[0-9]*%"
    # ポイントはない時がある
    if point is not None:
        matches = re.search(regex, point.text)
        loyalty_points = int(matches.group().split('%')[0])
    return loyalty_points


def build_attachments(kindle_books_list, point_threshold=20, discount_threshold=20):
    color = "good"

    attachments = []

    over_points_list = list(filter(lambda x: x[1]['loyalty_points'] >= point_threshold, kindle_books_list.items()))
    for id, kindle_book in over_points_list:
        text = "{} % ポイント還元".format(kindle_book['loyalty_points'])
        attachment = {
            "text": text,
            "color": color,
            "title": kindle_book['book_title'],
            "title_link": kindle_book['url'],
        }
        attachments.append(attachment)

    discount_list = list(filter(lambda x: x[1]['discount_rate'] >= discount_threshold, kindle_books_list.items()))
    for id, kindle_book in discount_list:
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


@cached(timeout=60*60)
def get_kindle_book(id, driver, url):
    kindle_book = {'url': url}
    soup = get_soup(driver, url)

    book_title = get_book_title(soup)
    kindle_book['book_title'] = book_title

    discount_rate = get_discount_rate(soup)
    kindle_book['discount_rate'] = discount_rate

    loyalty_points = get_loyalty_points(soup)
    kindle_book['loyalty_points'] = loyalty_points
    logger.debug("complete get_kindle_book: %s", kindle_book)
    return kindle_book


def lambda_handler(event, context):
    wish_list_url = event['wish_list_url']
    slack_incoming_web_hook = event['slack_incoming_web_hook']
    slack_channel = event['slack_channel']

    driver = get_web_driver()

    href_list = get_href_list(url=wish_list_url, driver=driver)

    kindle_books_list = {}
    for href in href_list:
        kindle_book_id = href.split('/')[2]
        wish_list_url = 'https://www.amazon.co.jp' + href
        kindle_book = get_kindle_book(id=id, driver=driver, url=wish_list_url)
        kindle_books_list[kindle_book_id] = kindle_book
    driver.close()

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
