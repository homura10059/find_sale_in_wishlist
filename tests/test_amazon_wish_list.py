import pytest

from find_sale_in_wish_list.amazon_wish_list import KindleBook
from find_sale_in_wish_list.headless_chrome import HeadlessChrome


@pytest.fixture(scope='module', autouse=True)
def kindle_book():
    headless_chrome = HeadlessChrome()
    kindle_book = KindleBook(headless_chrome)
    yield(kindle_book)
    headless_chrome.driver.close()


def test_get(kindle_book):
    url = "https://www.amazon.co.jp/dp/B018TPYYJU"
    book_attribute = kindle_book.get(url=url)
    print(book_attribute)
    assert book_attribute['url'] == url
    assert book_attribute['book_title'] is not None
    assert book_attribute['discount_rate'] >= 0
    assert book_attribute['discount_price'] >= 0
    assert book_attribute['price'] >= 0
    assert book_attribute['loyalty_points'] >= 0
    assert book_attribute['updated'] is not None

