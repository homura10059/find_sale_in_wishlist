from scraping.headless_chrome import HeadlessChrome


def test_init():
    hc = HeadlessChrome()
    hc.driver.close()
