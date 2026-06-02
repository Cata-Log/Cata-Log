# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Cata-Log - the central hub for grocery store catalogs
# Copyright (C) 2026 David Aderbauer & The Cata-Log Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy import create_engine, orm

from cata_log_hub.database.signals import *  # noqa: F403 # signals need to be brought into scope
from cata_log_hub.settings import get_settings

from .models import Catalog, ModelBase, Page, PageFile, Provider

DATABASE_URL = (
    get_settings().external_database_url
    or f"sqlite+pysqlite:///{get_settings().database_path / 'cata-log.sqlite3'}"
)

engine = create_engine(url=DATABASE_URL)

DBSession = orm.sessionmaker(bind=engine)


def get_db_session() -> Generator[orm.Session]:
    """Shortcut to get a new database session."""
    with DBSession() as db_session:
        yield db_session


depends_db_session = Depends(get_db_session)


__all__ = [
    "Catalog",
    "DBSession",
    "ModelBase",
    "Page",
    "PageFile",
    "Provider",
    "depends_db_session",
    "get_db_session",
]
