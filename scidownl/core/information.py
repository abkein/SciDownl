# -*- encoding: utf-8 -*-
"""Information implementations."""

from .base import BaseInformation


class UrlInformation(BaseInformation):
    """Information of url"""

    PROTOCOL_PREFIXES: list[str] = ["https://", "http://"]
    DEFAULT_PROTOCOL_PREFIX: str = PROTOCOL_PREFIXES[0]
    url: str

    def __init__(self, url: str) -> None:
        BaseInformation.__init__(self)
        self.url = url
        self["url"] = self.url

    def get_url(self) -> str:
        return self.url


class TitleInformation(BaseInformation):
    """Information of title"""

    title: str

    def __init__(self, title: str) -> None:
        BaseInformation.__init__(self)
        self.title = title
        self["title"] = self.title

    def get_title(self) -> str:
        return self.title


class PdfUrlTitleInformation(UrlInformation, TitleInformation):
    """Information with pdf url and title."""

    def __init__(self, url: str, title: str) -> None:
        UrlInformation.__init__(self, url)
        TitleInformation.__init__(self, title)
