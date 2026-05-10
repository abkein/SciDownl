# -*- coding: utf-8 -*-
"""Services to manipulate entities"""

from typing import Any

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from ..log import get_logger
from .entities import get_engine, ScihubUrl
from ..db.entities import create_tables

logger = get_logger()


class ScihubUrlService:
    engine: Engine
    session_class: sessionmaker[Any]

    def __init__(self, test: bool = False) -> None:
        create_tables()
        self.engine = get_engine(test=test)
        self.session_class = sessionmaker(bind=self.engine)

    def add_urls(self, urls: list[ScihubUrl] | None) -> None:
        if urls is None or len(urls) == 0:
            return
        session = self.session_class()
        for url in urls:
            try:
                session.add(url)
                session.commit()
            except Exception:
                session.rollback()
        session.close()

    def increment_success_times(self, url: str | None) -> None:
        if url is None:
            return
        session = self.session_class()
        try:
            session.query(ScihubUrl).filter_by(url=url).update({ScihubUrl.success_times: ScihubUrl.success_times + 1})
            session.commit()
        except Exception as e:
            logger.warning(f"Cannot increment success times: {url}, reason: {e}")
            session.rollback()
        session.close()

    def increment_failed_times(self, url: str | None) -> None:
        if url is None:
            return
        session = self.session_class()
        try:
            session.query(ScihubUrl).filter_by(url=url).update({ScihubUrl.failed_times: ScihubUrl.failed_times + 1})
            session.commit()
        except Exception as e:
            logger.warning(f"Cannot increment failed times: {url}, reason: {e}")
            session.rollback()
        session.close()

    def get_all_urls(self) -> list[ScihubUrl]:
        session = self.session_class()
        all_urls = session.query(ScihubUrl).all()
        session.close()
        return all_urls
