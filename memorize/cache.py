import time
import logzero
from logzero import logger

formatter = logzero.LogFormatter(
    fmt="%(asctime)s|%(filename)s:%(lineno)d|%(levelname)-7s : %(message)s",
)
logzero.formatter(formatter)


class Cache:
    in_memory_cache = {}

    def __init__(self, timeout=60*60):
        self.timeout = timeout

    def set(self, key, val):
        self.in_memory_cache[key] = {
            "time": time.time(),
            "value": val,
        }

    def get(self, key):
        cache = self.in_memory_cache.get(key)

        if cache is None:
            return None

        now = time.time()
        delta = now - cache["time"]
        if delta > self.timeout:
            self.in_memory_cache.pop(key)
            return None
        else:
            val = cache["value"]
            logger.debug("cache hit! key:%s, val:%s", key, val)
            return val


def cached(timeout=60*60):
    def decorator_cached(func):
        cache = Cache(timeout)

        def cached_func(*args, **kwargs):
            if kwargs.get("url") is None:
                key = args[0]
            else:
                key = kwargs.get("url")

            cached_val = cache.get(key)
            if cached_val is None:
                ret = func(*args, **kwargs)
                cache.set(key, ret)
                return ret
            else:
                return cached_val

        return cached_func
    return decorator_cached
