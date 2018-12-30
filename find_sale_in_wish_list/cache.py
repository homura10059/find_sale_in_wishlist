import time
import calendar
import logzero
from logzero import logger
import os
import boto3

from find_sale_in_wish_list import deserialize

formatter = logzero.LogFormatter(
    fmt="%(asctime)s|%(filename)s:%(lineno)d|%(levelname)-7s : %(message)s",
)
logzero.formatter(formatter)

endpoint_url = os.environ.get("dynamo_endpoint_url")

if endpoint_url is None:
    dynamo_db = boto3.resource('dynamodb')
else:
    dynamo_db = boto3.resource('dynamodb', endpoint_url=endpoint_url)

table_name = os.environ.get('CACHE_TABLE', default='kindle_book_cache')
TTL_KEY = "expired"


class Cache:

    def __init__(self, timeout=60*60):
        self.timeout = timeout
        self.table = dynamo_db.Table(table_name)

    def set(self, val: dict or list)-> None:
        val[TTL_KEY] = calendar.timegm(time.gmtime()) + self.timeout
        self.table.put_item(
            Item=val
        )
        logger.debug("cache set. val:%s", val)

    def get(self, key_name: str, key: str)-> None or dict or list:
        cache = self.table.get_item(
            Key={
                key_name: key
            }
        ).get("Item")

        if cache is None:
            return None

        cache = deserialize(cache)

        now = calendar.timegm(time.gmtime())
        expire = cache.get(TTL_KEY, 0)
        if now > expire:
            self.table.delete_item(
                Key={
                    key_name: key
                }
            )
            return None
        else:
            logger.debug("cache hit! key:%s, val:%s", key, cache)
            return cache


def cached(timeout=60*60):
    def decorator_cached(func):
        cache = Cache(timeout)

        def cached_func(*args, **kwargs):
            key_name = "url"
            if kwargs.get(key_name) is None:
                key = args[0]
            else:
                key = kwargs.get(key_name)

            cached_val = cache.get(key_name, key)
            if cached_val is None:
                ret = func(*args, **kwargs)
                cache.set(ret)
                return ret
            else:
                return cached_val

        return cached_func
    return decorator_cached
