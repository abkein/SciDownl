# -*- encoding: utf-8 -*-
"""Downloader implementation."""

import sys
from pathlib import Path
from typing import cast

import requests

from .base import BaseDownloader, BaseTask, BaseTaskStep
from .information import UrlInformation
from ..log import get_logger
from ..exception import DownloadException
from ..db.service import ScihubUrlService

logger = get_logger()


class UrlDownloader(BaseDownloader, BaseTaskStep):
    """Downloader of url."""

    service: ScihubUrlService

    def __init__(
        self, information: UrlInformation, task: BaseTask | None = None
    ) -> None:
        BaseDownloader.__init__(self, information)
        BaseTaskStep.__init__(self, task)
        self.information = information
        self.task = task
        self.service = ScihubUrlService()
        if self.task is not None:
            self.task.context["status"] = "downloading"

    def download(self, out: Path) -> str:
        """Download a url to out"""
        try:
            information = cast(UrlInformation, self.information)
            url = information.get_url()
            proxies = (
                cast(dict[str, str], self.task.context.get("proxies", {}))
                if self.task is not None
                else {}
            )
            timeout = (
                self.task.context.get("timeout", None)
                if self.task is not None
                else None
            )
            res = requests.get(url, stream=True, proxies=proxies, timeout=timeout)
            total_length_header = res.headers.get("content-length")

            with out.open("wb") as fp:
                if total_length_header is None:
                    # no content length header
                    fp.write(res.content)
                else:
                    download_length = 0
                    total_length = int(total_length_header)
                    bar_width = 50
                    for data in res.iter_content(chunk_size=4096):
                        download_length += len(data)
                        fp.write(data)
                        done_width = int(bar_width * download_length / total_length)
                        perc = int(100 * download_length / total_length)
                        sys.stdout.write(
                            "\r%3d%% [%s%s] %s/%s"
                            % (
                                perc,
                                "=" * done_width,
                                " " * (bar_width - done_width),
                                download_length,
                                total_length,
                            )
                        )
                        sys.stdout.flush()
                    sys.stdout.write("\n")
                    sys.stdout.flush()
            logger.info(f"↓ Successfully download the url to: {out.as_posix()}")

            if self.task is not None:
                self.task.context["out"] = out
                self.task.context["filename"] = out.name
        except Exception as e:
            if self.task is not None:
                self.task.context["status"] = "downloading_failed"
                self.task.context["error"] = e
                scihub_url = self.task.context.get("referer", None)
                scihub_url = scihub_url if isinstance(scihub_url, str) else None
                self.service.increment_failed_times(scihub_url)
            raise DownloadException(f"Error occurs when downloading {e}")
        return out.name
