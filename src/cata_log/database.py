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
    Connection,
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
from cata_log.providers import Provider as ProviderType
from src.cata_log.exceptions import ProviderMisconfiguredWarning

logger = logging.getLogger(__name__)

engine = create_engine(url=DATABASE_URL, echo=True)

DBSession = orm.sessionmaker(bind=engine)


def get_db_session() -> Generator[orm.Session]:
    """Shortcut to get a new database session."""
    with DBSession() as db_session:
        yield db_session


depends_db_session = Depends(get_db_session)


class TimestampMixin:
    """Mixin adding standard creation and update timestamps to an ORM model."""

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
    """ORM model for a cata_log instance configuration."""

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    name: orm.Mapped[str] = orm.mapped_column(unique=True)
    value: orm.Mapped[str] = orm.mapped_column()
    __tablename__ = "config"


class Provider(ModelBase, TimestampMixin):
    """ORM model for a catalog provider."""

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

    def get_provider_class(self) -> type[ProviderType]:
        """Get the class for this provider.

        Returns:
            The provider class.
        """
        provider_class = Provider.registry.get(self.class_id)
        if not provider_class:
            logger.error(
                "Provider class not found!",
                extra={
                    "provider_id": self.id,
                    "provider_class_id": self.class_id,
                },
            )
            raise ProviderMisconfiguredWarning
        return provider_class

    def get_provider_instance(self) -> ProviderType:
        """Get a class instance for this provider.

        Returns:
            The provider instance.
        """
        provider_class = self.get_provider_class()
        try:
            provider_instance = provider_class(**self.config)
        except TypeError as error:
            logger.exception(
                "Provider misconfigured!",
                extra={
                    "provider_id": self.id,
                    "provider_config": self.config,
                },
            )
            raise ProviderMisconfiguredWarning from error
        return provider_instance


class Catalog(ModelBase, TimestampMixin):
    """ORM model for a catalog."""

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
    __tablename__ = "catalogs"


class Page(ModelBase, TimestampMixin):
    """ORM model for a catalog page."""

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
def before_page_delete(
    mapper: orm.Mapper,  # noqa: ARG001  # required for event decorator
    connection: Connection,  # noqa: ARG001  # required for event decorator
    target: Page,
) -> None:
    """Event cleaning up a page file before deleting the page."""
    if target.storage_path:
        with contextlib.suppress(FileNotFoundError):
            os.remove(target.storage_path)


@event.listens_for(Provider, "after_insert")
def after_provider_insert(
    mapper: orm.Mapper,  # noqa: ARG001  # required for event decorator
    connection: Connection,
    target: Provider,
) -> None:
    """Event setting up a providers task after its insertion."""
    db_session = orm.Session(bind=connection)
    provider_class = ProviderType.registry.get(target.class_id)
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
def before_provider_delete(
    mapper: orm.Mapper,  # noqa: ARG001  # required for event decorator
    connection: Connection,
    target: Provider,
) -> None:
    """Event cleaning up a providers task before deleting the provider."""
    connection.execute(delete(PeriodicTask).where(PeriodicTask.id == target.task_id))
