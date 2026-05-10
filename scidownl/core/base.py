# -*- encoding: utf-8 -*-
"""Core base abstract classes"""
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from ..db.entities import ScihubUrl


class BaseTask(ABC):
    """Abstract task with a `run` method."""
    context: dict[str, Any]

    def __init__(self) -> None:
        self.context: dict[str, Any] = {}

    @abstractmethod
    def run(self) -> None:
        """Run the task."""
        raise NotImplementedError("Implement run method before calling it.")


class BaseTaskStep(ABC):
    """Abstract task step if a task.
    Every task step can access the task context.
    """
    task: BaseTask | None

    def __init__(self, task: BaseTask | None) -> None:
        self.task = task


class BaseSource(ABC, dict[str, str]):
    """Abstract source, which is a map that contains source item entries.
    """
    type: str

    def __init__(self) -> None:
        super().__init__()
        self.type = 'base'


class BaseContent(ABC):
    """Abstract content.
    """
    content: Any
    type: str

    def __init__(self, content: Any | None = None) -> None:
        self.content = "" if content is None else content
        self.type = 'base'


class BaseCrawler(ABC):
    """Abstract crawler with a `crawl` method.
    Crawler is used to output the Content with the given Source.
    """
    source: BaseSource

    def __init__(self, source: BaseSource) -> None:
        self.source = source

    @abstractmethod
    def crawl(self) -> BaseContent:
        """Crawl the source and returns the content of it.

        A typical crawling is accessing an url in the source, and
        returning the content with html string in it.
        """
        raise NotImplementedError("Implement crawl method before calling it.")


class BaseChecker(ABC):
    """Abstract checker with a `check` method.
    Checker is used to check the validity of Content.
    """
    content: BaseContent

    def __init__(self, content: BaseContent) -> None:
        self.content = content

    @abstractmethod
    def check(self) -> bool:
        """Check and return whether the content is valid."""
        raise NotImplementedError("Implement check method before calling it.")


class BaseInformation(ABC, dict[str, str]):
    """Abstract information, which is a map that contains information item entries.
    """
    type: str

    def __init__(self) -> None:
        super().__init__()
        self.type = 'base'


class BaseExtractor(ABC):
    """Abstract extractor with an `extract` method.
    Extractor is used to extract information from the Content.
    """
    content: BaseContent

    def __init__(self, content: BaseContent) -> None:
        self.content = content

    @abstractmethod
    def extract(self) -> BaseInformation:
        """Extract and return information from the content."""
        raise NotImplementedError("Implement extract method before calling it.")


class BaseDownloader(ABC):
    """Abstract downloader with a `download` method."""
    information: BaseInformation

    def __init__(self, information: BaseInformation) -> None:
        self.information = information

    @abstractmethod
    def download(self, out: str) -> str:
        """Download the information to local."""
        raise NotImplementedError("Implement download method before calling it.")


class DomainUpdater(ABC):
    """Abstract domain updater"""

    @abstractmethod
    def update_domains(self) -> list[str]:
        """Returns a sequence of urls."""
        raise NotImplementedError("Implement update_domain method before calling it.")


class ScihubUrlChooser(ABC):
    """Abstract chooser for choosing scihub url."""

    __chooser_type__: str = "base"

    @abstractmethod
    def next(self) -> ScihubUrl:
        """Returns the next scihub url or None if reach the end."""
        raise NotImplementedError("Implement next method before calling it.")

    def __iter__(self) -> Iterator[ScihubUrl]:
        return self

    def __next__(self) -> ScihubUrl:
        return self.next()

    def __len__(self) -> int:
        return 0
