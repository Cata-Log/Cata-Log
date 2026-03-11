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

import contextlib
import logging
import os
from collections.abc import Generator
from datetime import datetime

from celery_sqlalchemy_v2_scheduler.models import (
    CrontabSchedule,
    ModelBase,
    PeriodicTask,
)
from fastapi import Depends
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    create_engine,
    delete,
    event,
    func,
    orm,
)

from cata_log.constants import DATABASE_URL
from cata_log.providers import catalog_registry

engine = create_engine(url=DATABASE_URL, echo=True)

DBSession = orm.sessionmaker(bind=engine)


def get_db_session() -> Generator[orm.Session]:
    with DBSession() as db_session:
        yield db_session


depends_db_session = Depends(get_db_session)


class TimestampMixin:
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )

    updated_at: orm.Mapped[datetime] = orm.mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )


class Config(ModelBase, TimestampMixin):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(unique=True)
    value: orm.Mapped[str] = orm.mapped_column()
    __tablename__ = "config"


class Provider(ModelBase, TimestampMixin):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    class_id: orm.Mapped[str] = orm.mapped_column()
    config = Column(JSON, default={})
    task: orm.Mapped[PeriodicTask] = orm.relationship()
    task_id: orm.Mapped[int] = orm.mapped_column(
        ForeignKey(PeriodicTask.__tablename__ + ".id", ondelete="CASCADE"),
        nullable=True,
    )
    catalogs: orm.Mapped[list[Catalog]] = orm.relationship(
        back_populates="provider", cascade="all, delete-orphan"
    )
    __tablename__ = "providers"
    __table_args__ = (UniqueConstraint("class_id", "config"),)


class Catalog(ModelBase, TimestampMixin):
    __tablename__ = "catalogs"
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    valid_since: orm.Mapped[datetime] = orm.mapped_column(DateTime(timezone=True))
    valid_until: orm.Mapped[datetime] = orm.mapped_column(DateTime(timezone=True))
    provider: orm.Mapped[Provider] = orm.relationship(back_populates="catalogs")
    provider_id: orm.Mapped[int] = orm.mapped_column(
        ForeignKey(Provider.__tablename__ + ".id", ondelete="CASCADE"), nullable=False
    )
    pages: orm.Mapped[list[Page]] = orm.relationship(
        back_populates="catalog", cascade="all, delete-orphan"
    )


class Page(ModelBase, TimestampMixin):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    number: orm.Mapped[int] = orm.mapped_column()
    storage_path: orm.Mapped[str] = orm.mapped_column(unique=True)
    catalog: orm.Mapped[Catalog] = orm.relationship(back_populates="pages")
    catalog_id: orm.Mapped[int] = orm.mapped_column(
        ForeignKey(Catalog.__tablename__ + ".id", ondelete="CASCADE"), nullable=False
    )
    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("catalog_id", "number"),)


@event.listens_for(Page, "before_delete")
def before_page_delete(mapper, connection, target):
    if target.storage_path:
        with contextlib.suppress(FileNotFoundError):
            os.remove(target.storage_path)


@event.listens_for(Provider, "after_insert")
def after_provider_insert(mapper, connection, target):
    db_session = orm.Session(bind=connection)
    provider_class = catalog_registry.get(target.class_id)
    if not provider_class:
        logging.getLogger().critical("no provider class")
        return
    crontab = CrontabSchedule.from_schedule(db_session, provider_class.schedule)
    task = PeriodicTask(
        name=f"{target.class_id}-{target.config}",
        task="cata_log.tasks.fetch_catalog",
        args=f"[{target.id}]",
        crontab_id=crontab.id,
        enabled=True,
    )
    db_session.add(task)
    db_session.flush()
    connection.execute(
        Provider.__table__.update()
        .where(Provider.id == target.id)
        .values(task_id=task.id)
    )


@event.listens_for(Provider, "before_delete")
def before_provider_delete(mapper, connection, target):
    connection.execute(delete(PeriodicTask).where(PeriodicTask.id == target.task_id))
