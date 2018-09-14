import logzero
from logzero import logger
from time import sleep
from bs4 import BeautifulSoup
import re
import time
import calendar

from memorize.cache import cached
from scraping.headless_chrome import HeadlessChrome

formatter = logzero.LogFormatter(
    fmt="%(asctime)s|%(filename)s:%(lineno)d|%(levelname)-7s : %(message)s",
)
logzero.formatter(formatter)


class WishList:

    def __init__(self, url, headless_chrome=None):
        if headless_chrome is None:
            self.headless_chrome = HeadlessChrome()
        else:
            self.headless_chrome = headless_chrome
        html = self.__get_full_page_html(url)
        soup = BeautifulSoup(html, "html.parser")
        self.soup = soup

    def __get_full_page_html(self, url):
        driver = self.headless_chrome.driver
        driver.get(url)

        # ページ最下部までスクロール
        pause_time = 1
        scroll_height = 1280

        while True:
            logger.debug("scroll_height:%s, pause_time:%s, url:%s", scroll_height, pause_time, url)

            # スクロール
            driver.execute_script("window.scrollTo(0, {});".format(scroll_height))
            # 読み込み待ち
            sleep(pause_time)

            # HTMLを文字コードをUTF-8に変換してから取得
            html = driver.page_source.encode('utf-8')

            if self.is_end_of_page(html):
                break

            # 読み込み時間を延長
            pause_time += 1
            # スクロール距離を延長
            scroll_height *= 4

        logger.debug("complete get_full_page_html url:%s", url)

        html = driver.page_source.encode('utf-8')
        return html

    @staticmethod
    def is_end_of_page(html):

        soup = BeautifulSoup(html, "html.parser")

        # 読み込みが完了したか確認
        selector = "#g-items > div > span"
        list_end = soup.select_one(selector)
        return list_end is None

    def get_kindle_book_url_list(self):
        kindle_book_url_list = []
        for link in self.soup.findAll("a"):
            if link.get("href") is not None \
                    and "?coliid" in link.get('href') \
                    and "&ref" in link.get('href'):
                href = link.get('href').split("?")[0]
                kindle_book_url = 'https://www.amazon.co.jp' + href
                kindle_book_url_list.append(kindle_book_url)
        return kindle_book_url_list

    def get_kindle_books(self, url_list: list) -> dict:
        kindle_books_list = {}
        for url in url_list:
            kindle_book_id = url.split('/')[-2]
            kindle_book = self.get_kindle_book(url=url)
            kindle_books_list[kindle_book_id] = kindle_book
        return kindle_books_list

    @cached(timeout=60 * 60)
    def get_kindle_book(self, url):

        kindle_book = {'url': url}
        soup = self.headless_chrome.get_soup(url)

        book_title = self.__get_book_title(soup)

        discount_rate = self.__get_discount_rate(soup)
        kindle_book['discount_rate'] = discount_rate

        loyalty_points = self.__get_loyalty_points(soup)
        kindle_book['loyalty_points'] = loyalty_points

        kindle_book = {
            'url': url,
            'book_title': book_title,
            'discount_rate': discount_rate,
            'loyalty_points': loyalty_points,
            'updated': calendar.timegm(time.gmtime())
        }
        logger.debug("complete get_kindle_book: %s", kindle_book)
        return kindle_book

    @staticmethod
    def __get_book_title(soup)-> str:
        selector = "#ebooksProductTitle"
        book_title = soup.select_one(selector)
        if book_title is None:
            # 取れなかったら適当にselectorを返す
            return selector
        else:
            return book_title.text

    @staticmethod
    def __get_discount_rate(soup):
        selector = "#buybox > div > table > tbody > tr.kindle-price > td.a-color-price.a-size-medium.a-align-bottom > p"
        kindle_price = soup.select_one(selector)
        discount_rate = 0
        regex = r"[0-9]*%"
        if kindle_price is not None:
            matches = re.search(regex, kindle_price.text)
            discount_rate = int(matches.group().split('%')[0])
        return discount_rate

    @staticmethod
    def __get_loyalty_points(soup):
        selector = "#buybox > div > table > tbody > tr.loyalty-points > td.a-align-bottom"
        point = soup.select_one(selector)
        loyalty_points = 0
        regex = r"[0-9]*%"
        # ポイントはない時がある
        if point is not None:
            matches = re.search(regex, point.text)
            loyalty_points = int(matches.group().split('%')[0])
        return loyalty_points
