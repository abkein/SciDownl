# -*- coding: utf-8 -*-
"""JSON-backed storage entities."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..config import get_config

configs = get_config()


@dataclass(slots=True)
class ScihubUrl:
    url: str
    success_times: int = 0
    failed_times: int = 0

    def to_dict(self) -> dict[str, str | int]:
        return {
            "url": self.url,
            "success_times": self.success_times,
            "failed_times": self.failed_times,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ScihubUrl:
        url = data.get("url")
        success_times = data.get("success_times", 0)
        failed_times = data.get("failed_times", 0)

        if not isinstance(url, str):
            raise ValueError("ScihubUrl JSON record must contain a string 'url'.")
        if not isinstance(success_times, int):
            raise ValueError("ScihubUrl JSON record 'success_times' must be an integer.")
        if not isinstance(failed_times, int):
            raise ValueError("ScihubUrl JSON record 'failed_times' must be an integer.")
        return cls(url=url, success_times=success_times, failed_times=failed_times)

    def __repr__(self) -> str:
        return f"<ScihubUrl(url={self.url}, success_times={self.success_times}, failed_times={self.failed_times})>"


def get_storage_path(test: bool = False) -> Path:
    """Returns the JSON storage path."""
    par_dirpath = Path(__file__).resolve().parent.parent
    filename = "test-scidownl.json" if test else configs["global_db"]["db_name"]
    return par_dirpath / filename


def create_storage(test: bool = False) -> None:
    """Create the JSON storage file if it does not exist."""
    storage_path = get_storage_path(test=test)
    if storage_path.exists():
        return
    storage_path.write_text(json.dumps({"scihub_urls": []}, indent=2) + "\n", encoding="utf-8")


def create_tables(test: bool = False) -> None:
    """Compatibility wrapper for the old storage initialization API."""
    create_storage(test=test)
