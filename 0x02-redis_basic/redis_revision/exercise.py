#!/usr/bin/env python3
import redis
import uuid

from functools import wraps
from typing import Callable


def count_calls(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        key = fn.__qualname__
        self._redis.incr(key)
        return fn(self, *args, **kwargs)
    return wrapper

def call_history(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        input_key = f"{fn.__qualname__}:inputs"
        output_key = f"{fn.__qualname__}:outputs"
        output = fn(self, *args, **kwargs)
        self._redis.rpush(input_key, str(args))
        self._redis.rpush(output_key, str(output))
        return output
    return wrapper

class Cache():
    def __init__(self):
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    @call_history
    def store(self, data: str | bytes | int | float) -> str:
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key
    
    def get(self, key: str, fn: Callable = None):
        value = self._redis.get(key)
        return fn(value) if fn is not None else value
    
    def get_str(self, key: str) -> str | None:
        return self.get(key, fn=lambda d: d.decode("utf-8"))

    def get_int(self, key: str) -> int | None:
        return self.get(key, fn=int)
    
    
    
def replay(fn: Callable):
    """display the history of calls to a function"""
    instance = fn.__self__
    key = fn.__qualname__
    calls = instance.get_int(key)
    print(f"{key} was called {calls} times:")
    inputs = instance._redis.lrange(f"{fn.__qualname__}:inputs", 0, -1)
    outputs = instance._redis.lrange(f"{fn.__qualname__}:outputs", 0, -1)
    
    for input, output in zip(inputs, outputs):
        print(f"{key}({input}) -> {output}")
