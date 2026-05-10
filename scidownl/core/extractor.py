# -*- encoding: utf-8 -*-
"""Extractor implementations."""

import re

from bs4 import BeautifulSoup

from .base import BaseExtractor, BaseTask, BaseTaskStep
from .content import HtmlContent
from .information import PdfUrlTitleInformation, UrlInformation
from .chooser import scihub_url_choosers, AvailabilityFirstScihubUrlChooser
from ..exception import (
    PdfTagNotFoundException,
    # PdfUrlNotFoundException,
    ExtractException,
    CaptchaException,
)
from ..db.service import ScihubUrlService
from ..log import get_logger
from ..config import get_config

logger = get_logger()
configs = get_config()
FALLBACK_REFERER = "https://sci-hub.se"


def get_default_referer() -> str:
    scihub_url_chooser_type = configs["scihub.task"]["scihub_url_chooser_type"]
    chooser_cls = scihub_url_choosers.get(scihub_url_chooser_type, AvailabilityFirstScihubUrlChooser)
    chooser = chooser_cls()
    selected_url = chooser.next() if len(chooser) > 0 else None
    return FALLBACK_REFERER if selected_url is None else selected_url.url


class HtmlPdfExtractor(BaseExtractor, BaseTaskStep):
    """Pdf extractor to extract a pdf information from the html content."""

    # choose the first scihub url with the chooser defined in config.
    DEFAULT_REFERER: str = FALLBACK_REFERER
    service: ScihubUrlService
    pdf_tag_selector: str
    pdf_tag_attr: str
    _parser: str

    # Fallback selectors to try when the primary selector fails.
    # Sci-Hub has changed its HTML structure over time:
    #   - Old: <embed id="pdf" src="...">
    #   - New: <object type="application/pdf" data="...">
    FALLBACK_SELECTORS: list[tuple[str, str]] = [
        ('object[type="application/pdf"]', "data"),
        ("#pdf", "src"),
        ('embed[type="application/pdf"]', "src"),
        ("iframe", "src"),
    ]

    def __init__(self, content: HtmlContent, task: BaseTask | None = None) -> None:
        BaseExtractor.__init__(self, content)
        BaseTaskStep.__init__(self, task)
        self.task = task
        self.service = ScihubUrlService()

        if self.task is not None:
            self.task.context["status"] = "extracting"

        # using pdf_tag_selector, pdf_tag_attr in configs.
        self.pdf_tag_selector = configs["scihub.task.extractor"]["pdf_tag_selector"]
        self.pdf_tag_attr = configs["scihub.task.extractor"]["pdf_tag_attr"]
        self._parser = "html.parser"

    def extract(self) -> PdfUrlTitleInformation:
        try:
            url = self._extract_url()
            title = self._extract_title()

            info = PdfUrlTitleInformation(url, title)
            logger.info(f"* Extracted information: {info}")
            if self.task is not None:
                self.task.context["info"] = info
        except Exception as e:
            if self.task is not None:
                self.task.context["status"] = "extracting_failed"
                self.task.context["error"] = e
                scihub_url = self.task.context.get("referer", None)
                scihub_url = scihub_url if isinstance(scihub_url, str) else None
                self.service.increment_failed_times(scihub_url)
            raise ExtractException(f"Error occurs when extracting: {e}")

        return info

    def _extract_url(self) -> str:
        raw_url = self._extract_raw_url()

        for prefix in UrlInformation.PROTOCOL_PREFIXES:
            if prefix in raw_url:
                return raw_url

        url = raw_url.split("#")[0]
        if url.startswith("//"):
            url = UrlInformation.DEFAULT_PROTOCOL_PREFIX + url[2:]
        elif url.startswith("/"):
            fallback_referer = get_default_referer()
            if self.task is None:
                referer = fallback_referer
            else:
                referer_value = self.task.context.get("referer", fallback_referer)
                referer = referer_value if isinstance(referer_value, str) else fallback_referer
            url = referer + url
        return url

    def _extract_raw_url(self) -> str:
        """Extract pdf url from html content."""
        soup = BeautifulSoup(self.content.content, self._parser)

        # Detect captcha pages served by Sci-Hub
        title_tag = soup.title
        if title_tag and "robot" in title_tag.text.lower():
            raise CaptchaException("Sci-Hub returned a captcha page. Try again later or use a different domain.")
        if soup.find("div", class_="question"):
            raise CaptchaException("Sci-Hub returned a captcha page. Try again later or use a different domain.")

        # Try primary selector from config first
        pdf_tag = soup.select_one(self.pdf_tag_selector)  # pyright: ignore[reportUnknownMemberType]
        if pdf_tag is not None:
            raw_url = pdf_tag.attrs.get(self.pdf_tag_attr)
            if (raw_url is not None) and isinstance(raw_url, str):
                return raw_url

        # Try fallback selectors
        for selector, attr in self.FALLBACK_SELECTORS:
            tag = soup.select_one(selector)  # pyright: ignore[reportUnknownMemberType]
            if tag is not None:
                url = tag.attrs.get(attr)
                if (url is not None) and isinstance(url, str):
                    return url

        raise PdfTagNotFoundException(f"No pdf tag was found with selector '{self.pdf_tag_selector}' or any fallback selectors")

    def _extract_title(self) -> str:
        """Extract title from html content."""
        soup = BeautifulSoup(self.content.content, self._parser)
        soup_title = soup.title
        if soup_title is None or len(soup_title.text.strip()) == 0:
            return ""

        title_text = soup_title.text.strip()
        # Handle different Sci-Hub title formats:
        #   Old: "Sci-Hub | Title | DOI"
        #   New: "Sci-Hub. Title / Journal, Year"
        if "|" in title_text:
            parts = title_text.split("|")
            title = parts[1] if len(parts) > 1 else ""
        elif title_text.startswith("Sci-Hub."):
            # Remove "Sci-Hub. " prefix, then take text before " / "
            title = title_text[len("Sci-Hub.") :].strip()
            if " / " in title:
                title = title.split(" / ")[0]
        else:
            title = title_text
        return self._clean_title(title)

    @staticmethod
    def _clean_title(title: str) -> str:
        rstr = r"[\/\\\:\*\?\"\<\>\|]"  # / \ : * ? " < > |
        title = re.sub(rstr, " ", title)[:200]
        return title.strip()
