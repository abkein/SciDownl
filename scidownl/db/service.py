# -*- coding: utf-8 -*-
"""Services to manipulate JSON-backed entities."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from threading import RLock
from typing import ClassVar, cast

from ..log import get_logger
from .entities import ScihubUrl, create_storage, get_storage_path

logger = get_logger()


class ScihubUrlStore:
    _lock: ClassVar[RLock] = RLock()

    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path

    def read_urls(self) -> list[ScihubUrl]:
        with self._lock:
            return self._read_urls_unlocked()

    def write_urls(self, urls: list[ScihubUrl]) -> None:
        with self._lock:
            self._write_urls_unlocked(urls)

    def update_urls(self, updater: "UrlListUpdater") -> None:
        with self._lock:
            urls = self._read_urls_unlocked()
            updated_urls = updater(urls)
            self._write_urls_unlocked(updated_urls)

    def _read_urls_unlocked(self) -> list[ScihubUrl]:
        try:
            raw_text = self.storage_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []

        if raw_text.strip() == "":
            return []

        try:
            raw_payload: object = json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Cannot read SciHub URL storage {self.storage_path}: {e}")
            return []

        if not isinstance(raw_payload, dict):
            logger.warning(f"Cannot read SciHub URL storage {self.storage_path}: top-level value must be an object.")
            return []

        payload = cast(dict[str, object], raw_payload)
        raw_urls = payload.get("scihub_urls", [])
        if not isinstance(raw_urls, list):
            logger.warning(f"Cannot read SciHub URL storage {self.storage_path}: 'scihub_urls' must be a list.")
            return []

        urls: list[ScihubUrl] = []
        raw_url_records = cast(list[object], raw_urls)
        for raw_url in raw_url_records:
            if not isinstance(raw_url, dict):
                logger.warning(f"Skipping invalid SciHub URL record in {self.storage_path}: record must be an object.")
                continue
            raw_url_record = cast(dict[str, object], raw_url)
            try:
                urls.append(ScihubUrl.from_dict(raw_url_record))
            except ValueError as e:
                logger.warning(f"Skipping invalid SciHub URL record in {self.storage_path}: {e}")
        return urls

    def _write_urls_unlocked(self, urls: list[ScihubUrl]) -> None:
        payload = {"scihub_urls": [url.to_dict() for url in urls]}
        tmp_path = self.storage_path.with_name(f"{self.storage_path.name}.tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp_path.replace(self.storage_path)


UrlListUpdater = Callable[[list[ScihubUrl]], list[ScihubUrl]]


class ScihubUrlService:
    storage_path: Path
    store: ScihubUrlStore

    def __init__(self, test: bool = False) -> None:
        create_storage(test=test)
        self.storage_path = get_storage_path(test=test)
        self.store = ScihubUrlStore(self.storage_path)

    def add_urls(self, urls: list[ScihubUrl] | None) -> None:
        if urls is None or len(urls) == 0:
            return

        def add_missing(existing_urls: list[ScihubUrl]) -> list[ScihubUrl]:
            seen_urls = {existing_url.url for existing_url in existing_urls}
            for url in urls:
                if url.url in seen_urls:
                    continue
                existing_urls.append(url)
                seen_urls.add(url.url)
            return existing_urls

        self.store.update_urls(add_missing)

    def increment_success_times(self, url: str | None) -> None:
        if url is None:
            return

        def increment(existing_urls: list[ScihubUrl]) -> list[ScihubUrl]:
            for existing_url in existing_urls:
                if existing_url.url == url:
                    existing_url.success_times += 1
                    break
            return existing_urls

        self.store.update_urls(increment)

    def increment_failed_times(self, url: str | None) -> None:
        if url is None:
            return

        def increment(existing_urls: list[ScihubUrl]) -> list[ScihubUrl]:
            for existing_url in existing_urls:
                if existing_url.url == url:
                    existing_url.failed_times += 1
                    break
            return existing_urls

        self.store.update_urls(increment)

    def get_all_urls(self) -> list[ScihubUrl]:
        return self.store.read_urls()
