from collections.abc import Callable
from typing import Any, TypeVar

_F = TypeVar("_F", bound=Callable[..., Any])


class Command:
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


class Group(Command):
    def command(self, *args: Any, **kwargs: Any) -> Callable[[_F], _F]: ...


def group(*args: Any, **kwargs: Any) -> Callable[[_F], Group]: ...
def help_option(*args: Any, **kwargs: Any) -> Callable[[_F], _F]: ...
def option(*args: Any, **kwargs: Any) -> Callable[[_F], _F]: ...
