"""
TODO:

The function `add` accepts two arguments and returns a value, they all have the same type.
"""

from typing import List, overload, Any


@overload
def add(a: int, b: int) -> int:
    pass


@overload
def add(a: str, b: str) -> str:
    pass


@overload
def add(a: List[str], b: List[str]) -> List[str]:
    pass


def add(a: Any, b: Any) -> Any:
    return a + b
