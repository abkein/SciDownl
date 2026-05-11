# -*- coding: utf-8 -*-

import sys
import logging


def get_logger(name: str = "default") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    sout_handler = logging.StreamHandler(stream=sys.stdout)
    sout_handler.setLevel(logging.DEBUG)
    return logger
