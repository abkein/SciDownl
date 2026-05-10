# -*- encoding: utf-8 -*-
"""Source implementations."""

from collections.abc import Callable
from typing import Any

from .base import BaseSource
from ..exception import EmptyDoiException, EmptyPmidException, EmptyTitleException


class DoiSource(BaseSource):
    """A DOI source dict."""

    DOI_PROTOCOLS: list[str] = ["http://", "https://"]
    doi: str
    protocol: str

    def __init__(self, doi: Any) -> None:
        super().__init__()
        self.doi = self._clean_doi(doi)
        self.protocol = self._extract_protocol(doi)
        self.type = "doi"
        self[self.type] = self.doi
        self["protocol"] = self.protocol

    @staticmethod
    def _clean_doi(doi: Any) -> str:
        if doi is None:
            raise EmptyDoiException("Empty doi is given")
        if not isinstance(doi, str):
            raise TypeError(f"Doi must be a string, got a {type(doi)} instead")
        if len(doi) == 0:
            raise EmptyDoiException("Empty doi is given")

        doi_str = doi
        for proto in DoiSource.DOI_PROTOCOLS:
            doi_str = doi_str.replace(proto, "")
        return doi_str

    @staticmethod
    def _extract_protocol(doi: Any) -> str:
        if not isinstance(doi, str):
            return "https"
        for proto in DoiSource.DOI_PROTOCOLS:
            if proto in doi:
                return str(proto.split(":")[0])
        return "https"

    def get_doi(self) -> str:
        return self.doi

    def get_protocol(self) -> str:
        return self.protocol

    def __repr__(self) -> str:
        return f"DoiSource[type={self.type}, id={self.doi}]"


class PmidSource(BaseSource):
    """A PMID source dict."""

    pmid: str

    def __init__(self, pmid: Any) -> None:
        super().__init__()
        self.pmid = self._clean_pmid(pmid)
        self.type = "pmid"
        self[self.type] = self.pmid

    @staticmethod
    def _clean_pmid(pmid: Any) -> str:
        if pmid is None:
            raise EmptyPmidException("Empty pmid is given")
        if not isinstance(pmid, str) and not isinstance(pmid, int) or isinstance(pmid, bool):
            raise TypeError(f"PMID must be either a string or an integer, got a {type(pmid)} instead")

        pmid_str = str(pmid)
        if len(pmid_str) == 0:
            raise EmptyPmidException("Empty pmid is given")
        return pmid_str

    def get_pmid(self) -> str:
        return self.pmid

    def __repr__(self) -> str:
        return f"PmidSource[type={self.type}, id={self.pmid}]"


class TitleSource(BaseSource):
    """A title source dict."""

    title: str

    def __init__(self, title: Any) -> None:
        super().__init__()
        self.title = self._clean_title(title)
        self.type = "title"
        self[self.type] = self.title

    @staticmethod
    def _clean_title(title: Any) -> str:
        if title is None:
            raise EmptyTitleException("Empty title is given")
        if not isinstance(title, str):
            raise TypeError(f"Title must be either a string or an integer, got a {type(title)} instead")

        title_str = str(title).strip()
        if len(title_str) == 0:
            raise EmptyTitleException("Empty title is given")
        return title_str

    def get_title(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"TitleSource[type={self.type}, id={self.title}]"


source_classes: dict[str, Callable[[Any], BaseSource]] = {
    "doi": DoiSource,
    "DOI": DoiSource,
    "pmid": PmidSource,
    "PMID": PmidSource,
    "title": TitleSource,
    "TITLE": TitleSource,
}
