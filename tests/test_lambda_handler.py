from unittest import TestCase

from find_sale_in_wish_list.headless_chrome import HeadlessChrome
from lambda_handler.notifier import get_kindle_books


class TestNotifier(TestCase):

    def test_get_kindle_books(self):
        event = {
            'wish_list_url': 'http://amzn.asia/4jy4esM',
            'expired': 1545440835,
            'user_id': '92676047-1ce7-4080-bd44-10e3fc63a16d',
            'description': 'マンガ',
            'threshold': {
                'discount_rate': 20,
                'points': 20
            }
        }
        try:
            headless_chrome = HeadlessChrome()
            get_kindle_books(event, headless_chrome)
            headless_chrome.driver.close()
        except:
            self.fail()
