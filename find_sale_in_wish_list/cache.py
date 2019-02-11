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
NINETY_DAYS = 60 * 60 * 24 * 90  # best score 含めた cache の保持期限


class Cache:

    def __init__(self, timeout=60*60):
        self.timeout = timeout
        self.table = dynamo_db.Table(table_name)

    def set(self, val: dict)-> None:
        """
        cache data を更新する
        :param val:
        :return:
        """
        val[TTL_KEY] = calendar.timegm(time.gmtime()) + NINETY_DAYS

        if val.get("best", None):
            best = val["best"]  # type: dict
            latest = val["latest"]  # type: dict
            self.update_best_score("discount_rate", latest, best, True)
            self.update_best_score("discount_price", latest, best, True)
            self.update_best_score("price", latest, best, False)
            self.update_best_score("loyalty_points", latest, best, True)
        else:
            val["best"] = val["latest"]

        self.table.put_item(
            Item=val
        )
        logger.debug("cache set. val:%s", val)

    @staticmethod
    def update_best_score(key: str, latest: dict, best: dict, big_is_win: bool):
        """
        best score を更新する
        :param key:
        :param latest:
        :param best:
        :param big_is_win: 数字が大きい方をbestをする場合は True
        :return:
        """
        if best.get(key):
            best[key] = latest[key]
            best["updated"] = latest["updated"]

        if big_is_win:
            if latest[key] > best[key]:
                best[key] = latest[key]
                best["updated"] = latest["updated"]
        else:
            if latest[key] < best[key]:
                best[key] = latest[key]
                best["updated"] = latest["updated"]

    def get(self, key_name: str, key: str)-> None or dict or list:
        """
        cache data を取得する.
        :param key_name:
        :param key:
        :return:
        """
        cache = self.table.get_item(
            Key={
                key_name: key
            }
        ).get("Item")

        if cache is None:
            logger.debug("no cache data. key:%s", key)
            return None

        cache = deserialize(cache)

        now = calendar.timegm(time.gmtime())
        expire = cache["latest"].get("updated", 0) + self.timeout
        if now > expire:
            logger.debug("cache is expired. key:%s", key)
            return None
        else:
            logger.debug("cache hit. key:%s, val:%s", key, cache)
            return cache


def cached(timeout=60*60):
    """
    タイムアウトを引数にとって cache する為のデコレータを返却する関数
    :param timeout: タイムアウト
    :return: デコレータ
    """

    def decorator_cached(func):
        """
        cache処理する為のデコレータ
        :param func: 関数
        :return: 装飾された関数
        """
        cache = Cache(timeout)

        def cached_func(*args, **kwargs):
            """
            cash処理
            :param args: 引数
            :param kwargs: キーワード引数
            :return: キャッシュ処理した戻り値
            """
            key_name = "url"

            if kwargs.get(key_name) is None:
                raise AttributeError("required 'url' in kwargs")
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
