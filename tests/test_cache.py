from find_sale_in_wish_list.cache import Cache
from find_sale_in_wish_list.cache import cached
from time import sleep


@cached()
def example_func(url):
    return url + "_example"


def test_timeout():
    cache = Cache(timeout=0.1)
    cache.set("key", "val")
    sleep(0.1)
    val = cache.get("key")
    assert val is None


def test_get():
    cache = Cache()
    cache.set("key", "val")
    val = cache.get("key")
    assert val == "val"


def test_cached_func():
    example_func(url="aaaa")
    example_func(url="aaaa")
    example_func("aaaa")
