# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from configparser import ConfigParser
from threading import RLock


class GlobalConfig:
    _lock: RLock = RLock()
    _config: ConfigParser | None = None
    config_fpath: Path = Path(__file__).resolve().parent / "config/global.ini"

    def _config_init(self) -> ConfigParser:
        # Check if config file exists.
        if not (self.config_fpath.exists() and self.config_fpath.is_file()):
            print(f"Config file not found: {self.config_fpath.as_posix()}")
            sys.exit(2)

        # Read configs.
        configs = ConfigParser()
        configs.read(self.config_fpath)
        return configs

    @staticmethod
    def get_config() -> ConfigParser:
        if GlobalConfig._config is None:
            with GlobalConfig._lock:
                if GlobalConfig._config is None:
                    GlobalConfig._config = GlobalConfig()._config_init()
        return GlobalConfig._config


def get_config() -> ConfigParser:
    return GlobalConfig.get_config()
