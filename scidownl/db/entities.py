# -*- coding: utf-8 -*-
"""Entities of tables"""

from pathlib import Path
from typing import Any, cast

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base

from ..config import get_config

Base: Any = declarative_base()
configs = get_config()


def get_engine(echo: bool = False, test: bool = False) -> Engine:
    """Returns the db engine.

    :param echo: if True, the Engine will log all statements.
    :param test: if True, using test db instead.
    :returns :class:`sqlalchemy._engine.Engine` instance.
    """
    par_dirpath = Path(__file__).resolve().parent.parent
    dbname = "test-scidownl.db" if test else configs["global_db"]["db_name"]
    db_path = par_dirpath / dbname
    engine = create_engine(f"sqlite:///{db_path}?check_same_thread=False", echo=echo)
    return engine


def create_tables(test: bool = False) -> None:
    """Create all tables that are not exist.

    :param test: if True, using test db instead.
    """
    engine = get_engine(test=test)
    Base.metadata.create_all(engine, checkfirst=True)


class ScihubUrl(Base):  # type: ignore[misc]
    url: str
    success_times: int
    failed_times: int

    __tablename__: str = "scihub_url"

    url = cast(str, Column(String(50), primary_key=True))
    success_times = cast(int, Column(Integer, default=0))
    failed_times = cast(int, Column(Integer, default=0))

    def __init__(self, url: str, success_times: int = 0, failed_times: int = 0) -> None:
        self.url = url
        self.success_times = success_times
        self.failed_times = failed_times

    def __repr__(self) -> str:
        return f"<ScihubUrl(url={self.url}, " f"success_times={self.success_times}, " f"failed_times={self.failed_times})>"
