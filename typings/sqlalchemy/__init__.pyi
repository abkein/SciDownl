from typing import Any

from .engine import Engine


class Column:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def __add__(self, other: int) -> Any: ...


class Integer:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...


class String:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...


def create_engine(*args: Any, **kwargs: Any) -> Engine: ...
