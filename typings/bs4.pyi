from typing import Any


class Tag:
    attrs: dict[str, Any]
    text: str

    def get_text(self) -> str: ...


class BeautifulSoup:
    title: Tag | None

    def __init__(self, markup: str | bytes, features: str | None = None, **kwargs: Any) -> None: ...
    def select_one(self, selector: str) -> Tag | None: ...
