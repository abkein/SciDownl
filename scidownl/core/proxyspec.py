# -*- encoding: utf-8 -*-
"""In case curl_cffi isn't installed"""

from typing import TypedDict


class ProxySpec(TypedDict, total=False):
    all: str
    http: str
    https: str
    ws: str
    wss: str
