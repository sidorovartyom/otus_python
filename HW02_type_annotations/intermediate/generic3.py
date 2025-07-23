"""
TODO:

The function `add` accepts one argument and returns a value, they all have the same type.
The type can only be int or subclasses of int.
"""

from typing import TypeVar, Type, cast, overload

T = TypeVar('T', bound=int)


def add(a: T) -> T:
    if not isinstance(a, int):
        raise

    return type(a)(int(a) + 1)