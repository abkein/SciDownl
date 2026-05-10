# -*- coding: utf-8 -*-
"""Crawler implementations."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from curl_cffi import requests as requests
    from curl_cffi import ProxySpec

    HAS_CURL_CFFI = True
else:
    try:
        from curl_cffi import requests as requests
        from curl_cffi import ProxySpec

        HAS_CURL_CFFI = True
    except (ModuleNotFoundError, ImportError):
        import requests
        from .proxyspec import ProxySpec

        HAS_CURL_CFFI = False  # pyright: ignore[reportConstantRedefinition]

from typing import cast

from .content import HtmlContent
from .captcha import solve_altcha, is_captcha_page
from .base import BaseCrawler, BaseSource, BaseTaskStep, BaseTask
from ..log import get_logger
from ..exception import CrawlException
from ..db.service import ScihubUrlService

logger = get_logger()


class ScihubCrawler(BaseCrawler, BaseTaskStep):
    """Crawler of a scihub source."""

    OK_STATUS_CODES: list[int] = [200]
    scihub_url: str
    sess: requests.Session
    service: ScihubUrlService

    def __init__(self, source: BaseSource, scihub_url: str, task: BaseTask | None = None) -> None:
        BaseCrawler.__init__(self, source)
        BaseTaskStep.__init__(self, task)
        self.scihub_url = scihub_url
        if HAS_CURL_CFFI:
            self.sess = requests.Session(impersonate="chrome")
        else:
            self.sess = requests.Session()
        self.service = ScihubUrlService()

        if self.task is not None:
            self.task.context["source"] = source
            self.task.context["referer"] = scihub_url
            self.task.context["status"] = "crawling"
            self.task.context["session"] = self.sess

    def _fetch(self, proxies: ProxySpec, timeout: int | None = None) -> requests.Response:
        """Fetch the page from Sci-Hub. Uses GET with path for DOI/PMID,
        falls back to POST if GET returns empty content."""
        source_id = self.source[self.source.type]

        res: requests.Response
        if self.source.type == "title":
            # Title searches must use POST form data
            res = self.sess.post(
                self.scihub_url,
                data={"request": source_id},
                proxies=proxies,
                timeout=timeout,
            )
        else:
            # DOI/PMID: try GET first, fall back to POST if empty
            url = f"{self.scihub_url.rstrip('/')}/{source_id}"
            res = self.sess.get(url, proxies=proxies)
            if res.status_code in ScihubCrawler.OK_STATUS_CODES and len(res.content) == 0:
                logger.info("GET returned empty body, retrying with POST...")
                res = self.sess.post(self.scihub_url, data={"request": source_id}, proxies=proxies)
        return res

    def crawl(self) -> HtmlContent:
        try:
            proxies: ProxySpec = cast(ProxySpec, self.task.context.get("proxies", {})) if self.task is not None else {}
            timeout = self.task.context.get("timeout", None) if self.task is not None else None
            logger.info(f"<- Request: scihub_url={self.scihub_url}, source={self.source}, proxies={proxies}")

            res = self._fetch(proxies=proxies, timeout=timeout)
            logger.info(f"-> Response: status_code={res.status_code}, content_length={len(res.content)}")

            if res.status_code not in ScihubCrawler.OK_STATUS_CODES:
                raise RuntimeError(f"Error occurs when crawling source: {self.source}")

            html_text = res.content.decode(errors="replace")

            # Handle CAPTCHA if present
            if is_captcha_page(html_text):
                logger.info("Captcha detected, solving...")
                solved = solve_altcha(self.sess, self.scihub_url, html_text, proxies)
                if solved:
                    # Re-fetch the page after solving captcha
                    res = self._fetch(proxies)
                    html_text = res.content.decode()
                    logger.info(f"-> Post-captcha response: status_code={res.status_code}, " f"content_length={len(html_text)}")
                    if is_captcha_page(html_text):
                        raise RuntimeError("Still getting captcha after solving it")
                else:
                    raise RuntimeError("Failed to solve captcha")

            content = HtmlContent(html_text)

            if self.task is not None:
                self.task.context["content"] = content
                self.task.context["status"] = "crawled"
            return content
        except Exception as e:
            if self.task is not None:
                self.task.context["status"] = "crawling_failed"
                self.task.context["error"] = e
                self.service.increment_failed_times(self.scihub_url)
            raise CrawlException(f"Error occurs when crawling: {e}")

    def __del__(self) -> None:
        self.sess.close()
