import time
import calendar
import logzero
from logzero import logger
import os
import boto3


formatter = logzero.LogFormatter(
    fmt="%(asctime)s|%(filename)s:%(lineno)d|%(levelname)-7s : %(message)s",
)
logzero.formatter(formatter)

endpoint_url = os.environ.get("dynamo_endpoint_url")

if endpoint_url is None:
    dynamo_db = boto3.resource('dynamodb')
else:
    dynamo_db = boto3.resource('dynamodb', endpoint_url=endpoint_url)

table = dynamo_db.Table('kindle_book_cache')


class Cache:

    def __init__(self, timeout=60*60):
        self.timeout = timeout

    def set(self, val: dict or list)-> None:
        val["expire"] = calendar.timegm(time.gmtime()) + self.timeout
        table.put_item(
            Item=val
        )
        logger.debug("cache set. val:%s", val)

    @staticmethod
    def get(key_name: str, key: str)-> None or dict or list:
        cache = table.get_item(
            Key={
                key_name: key
            }
        ).get("Item")

        if cache is None:
            return None

        now = calendar.timegm(time.gmtime())
        expire = cache["expire"]
        if now > expire:
            table.delete_item(
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
