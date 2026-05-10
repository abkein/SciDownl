# -*- coding: utf-8 -*-
import sys
from threading import RLock
from configparser import ConfigParser
from typing import Any, Callable

from loguru import logger

from .config import get_config


configs: ConfigParser = get_config()


class LoggerLoader:
    _init_status: bool = False
    _lock: RLock = RLock()
    _loggers = {}

    def _log_init(self):
        """Initialize loggings."""
        # Load log configs
        log_level = configs['log']['console_log_level']
        log_format = configs['log']['console_log_format']

        logger.remove()
        loggers = {}
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
    def _make_filter(name: str) -> Callable[[dict[str, dict[str, Any]]], bool]:
        def f(record: dict[str, dict[str, Any]]) -> bool:
            return record["extra"].get("name") == name
        return f

    @staticmethod
    def load(logger_name: str):
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


def get_logger(name: str | None = None):
    name = name or 'default'
    return LoggerLoader.load(name)
