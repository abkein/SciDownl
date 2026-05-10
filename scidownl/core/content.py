# -*- coding: utf-8 -*-
"""Content implementations."""

from .base import BaseContent


class HtmlContent(BaseContent):
    """Content stores html string."""

    content: str

    def __init__(self, html: str | None = None) -> None:
        super().__init__(html)
        self.type = "html"

    def __repr__(self) -> str:
        return f"HtmlContent[html = {self.content}]"

    def __len__(self) -> int:
        return len(self.content)


class JsonContent(BaseContent):
    """Content stores JSON object."""

    content: dict[str, object]

    def __init__(self, json: dict[str, object] | None = None) -> None:
        super().__init__(json)
        self.type = "json"

    def __repr__(self) -> str:
        return f"JsonContent[json = {self.content}]"

    def __len__(self) -> int:
        return len(self.content)
