# -*- coding: utf-8 -*-
import os
import sys
from configparser import ConfigParser
from threading import RLock


class GlobalConfig(object):
    _lock: RLock = RLock()
    _config: ConfigParser | None = None
    package_dir: str = os.path.dirname(__file__)
    config_fpath: str = os.path.abspath(os.path.join(package_dir, 'config/global.ini'))

    def _config_init(self) -> ConfigParser:
        # Check if config file exists.
        if not os.path.isfile(self.config_fpath):
            print("Config file not found: %s" % self.config_fpath)
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
