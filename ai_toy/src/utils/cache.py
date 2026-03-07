# -*- coding: utf-8 -*-
"""缓存装饰器"""

import functools
import hashlib
import time
from typing import Any, Callable


def cache_with_ttl(ttl_seconds: int = 300):
    """带 TTL 的缓存装饰器"""

    def decorator(func: Callable):
        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = hashlib.md5(f"{args}{kwargs}".encode()).hexdigest()
            current_time = time.time()

            if key in cache:
                cached_value, timestamp = cache[key]
                if current_time - timestamp < ttl_seconds:
                    return cached_value

            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            return result

        return wrapper

    return decorator
