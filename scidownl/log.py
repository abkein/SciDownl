# -*- coding: utf-8 -*-
import sys
from threading import RLock
from configparser import ConfigParser
from typing import Any, Callable, cast

from loguru import logger

from .config import get_config


configs: ConfigParser = get_config()


class LoggerLoader:
    _init_status: bool = False
    _lock: RLock = RLock()
    _loggers: dict[str, Any] = {}

    def _log_init(self) -> dict[str, Any]:
        """Initialize loggings."""
        # Load log configs
        log_level = configs['log']['console_log_level']
        log_format = configs['log']['console_log_format']

        logger.remove()
        loggers: dict[str, Any] = {}
        # Add default logger
        default_logger_name = 'default'
        logger.add(sys.stderr,
                   level=log_level,
                   filter=self._make_filter(name=default_logger_name),
                   format=log_format)
        default_logger = logger.bind(name=default_logger_name)
        loggers[default_logger_name] = default_logger
        default_logger.debug("Registered the default logger")
        return loggers

    @staticmethod
    def _make_filter(name: str) -> Callable[[Any], bool]:
        def f(record: Any) -> bool:
            record_dict = cast(dict[str, Any], record) if isinstance(record, dict) else {}
            extra = cast(dict[str, Any], record_dict.get("extra", {}))
            return bool(extra.get("name") == name)
        return f

    @staticmethod
    def load(logger_name: str) -> Any:
        """Returns the loguru.Logger based on logger name.

        :param logger_name: Logger name.
        :return: a loguru.Logger.
        """
        if not LoggerLoader._init_status:
            with LoggerLoader._lock:
                if not LoggerLoader._init_status:
                    LoggerLoader._loggers = LoggerLoader()._log_init()
                    LoggerLoader._init_status = True
        return LoggerLoader._loggers.get(logger_name)


def get_logger(name: str | None = None) -> Any:
    name = name or 'default'
    return LoggerLoader.load(name)
