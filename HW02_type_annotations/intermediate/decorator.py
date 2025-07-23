"""
TODO:

Define a decorator that wraps a function and returns a function with the same signature.
"""
from typing import Callable, TypeVar, ParamSpec

R = TypeVar('R')
P = ParamSpec('P')


def decorator(func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)

    return wrapper
