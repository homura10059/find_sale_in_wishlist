import logzero
from logzero import logger
from selenium import webdriver
import os
import platform
from bs4 import BeautifulSoup

formatter = logzero.LogFormatter(
    fmt="%(asctime)s|%(filename)s:%(lineno)d|%(levelname)-7s : %(message)s",
)
logzero.formatter(formatter)


class HeadlessChrome:

    def __init__(self):
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
        self.driver = driver

    def get_soup(self, url):
        self.driver.get(url)
        html = self.driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, "html.parser")
        return soup
