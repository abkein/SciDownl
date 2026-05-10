# -*- encoding: utf-8 -*-
"""Task implementations."""

from pathlib import Path
from collections.abc import Callable
from typing import Any

from .base import BaseSource, BaseTask, ScihubUrlChooser
from .source import DoiSource, source_classes
from .crawler import ScihubCrawler
from .extractor import HtmlPdfExtractor
from .downloader import UrlDownloader
from .chooser import AvailabilityFirstScihubUrlChooser, scihub_url_choosers
from .updater import CrawlingScihubDomainUpdater
from ..log import get_logger
from ..config import get_config
from ..db.service import ScihubUrlService

logger = get_logger()
configs = get_config()

scihub_url_chooser_type = configs["scihub.task"]["scihub_url_chooser_type"]
default_chooser_cls = scihub_url_choosers.get(scihub_url_chooser_type, AvailabilityFirstScihubUrlChooser)


class ScihubTask(BaseTask):
    source_keyword: Any
    scihub_url_chooser_cls: type[ScihubUrlChooser]
    scihub_url_chooser: ScihubUrlChooser
    scihub_url: str | None
    source_class: Callable[[Any], BaseSource]
    out: Path | None
    proxies: dict[str, str]
    service: ScihubUrlService
    updater: CrawlingScihubDomainUpdater
    timeout: int | None

    def __init__(
        self,
        source_keyword: Any,
        source_type: str = "doi",
        scihub_url: str | None = None,
        scihub_url_chooser_cls: type[ScihubUrlChooser] = default_chooser_cls,
        out: Path | None = None,
        proxies: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> None:
        super().__init__()
        self.source_keyword = source_keyword
        self.scihub_url_chooser_cls = scihub_url_chooser_cls
        self.scihub_url_chooser = self.scihub_url_chooser_cls()
        self.scihub_url = scihub_url
        self.source_class = source_classes.get(source_type, DoiSource)
        self.out = out
        self.proxies = proxies or {}
        self.timeout = timeout
        self.context["status"] = "initialized"
        self.context["proxies"] = self.proxies
        self.context["timeout"] = self.timeout
        self.service = ScihubUrlService()
        self.updater = CrawlingScihubDomainUpdater()

    def run(self) -> Path | None:
        if self.scihub_url is not None:
            logger.info(f"Choose the scihub url: {self.scihub_url}")
            return self._run(self.scihub_url)

        # Always refresh scihub domains from the online source
        # to ensure we have the latest working mirrors.
        try:
            self.updater.update_domains()
            self.scihub_url_chooser = self.scihub_url_chooser_cls()
        except Exception as e:
            logger.warning(f"Failed to refresh SciHub domains: {e}")
            if len(self.scihub_url_chooser) == 0:
                logger.error("No SciHub domains available.")
                return None

        for i, scihub_url in enumerate(self.scihub_url_chooser):
            try:
                logger.info(f"Choose scihub url [{i}]: {scihub_url.url}")
                return self._run(scihub_url.url)
            except Exception:
                logger.warning(f"Error occurs, task status: {self.context['status']}, error: {self.context['error']}")
                continue
        logger.error(f"Failed to download the paper: {self.source_keyword}. Please try again.")
        return None

    def _run(self, scihub_url: str) -> Path:
        source = self.source_class(self.source_keyword)
        crawler = ScihubCrawler(source, scihub_url, self)
        content = crawler.crawl()

        extractor = HtmlPdfExtractor(content, self)
        pdf_url_title_info = extractor.extract()

        if self.out is None:
            # Using title as the filename and save to current directory.
            self.out = Path(pdf_url_title_info["title"] + ".pdf")
        else:
            dirpath = self.out.parent
            filename = self.out.name
            if not dirpath.exists():
                dirpath.mkdir(parents=True, exist_ok=True)
            if len(filename) == 0:
                filename = pdf_url_title_info.get_title() + ".pdf"
            if not (filename.endswith("pdf") or filename.endswith("PDF")):
                filename += ".pdf"
            self.out = dirpath / filename

        downloader = UrlDownloader(pdf_url_title_info, self)
        downloader.download(self.out)
        referer_url = self.context.get("referer", None)
        referer_url = referer_url if isinstance(referer_url, str) else None
        self.service.increment_success_times(referer_url)
        return self.out
