#!/usr/bin/env python3
import requests

from functools import wraps
from typing import Callable
import redis

redis = redis.Redis()


def count_visits(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        key = fn.__qualname__
        redis.incr(key)
        calls = redis.get(key)
        print(f"{key} was called {calls} times:")
        return fn(*args, **kwargs)
    return wrapper


@count_visits
def get_page(url: str) -> str:
    """get html of a page and return it as a string"""
    response = requests.get(url)
    return response.text

# test the function
print(get_page("https://example.com"))
print(get_page("https://example.com"))