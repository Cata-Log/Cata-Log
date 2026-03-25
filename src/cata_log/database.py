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
from datetime import UTC, datetime
from io import BytesIO

from celery_sqlalchemy_v2_scheduler.models import (
    CrontabSchedule,
    ModelBase,
    PeriodicTask,
)
from fastapi import Depends
from PIL import Image
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
from cata_log.exceptions import (
    ProviderBrokenWarning,
    ProviderMisconfiguredWarning,
)
from cata_log.providers import Provider as ProviderType

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
    is_broken: orm.Mapped[bool] = orm.mapped_column(default=False)
    is_misconfigured: orm.Mapped[bool] = orm.mapped_column(default=False)
    __tablename__ = "providers"
    __table_args__ = (UniqueConstraint("class_id", "config"),)

    def get_provider_class(self) -> type[ProviderType]:
        """Get the class for this provider.

        Returns:
            The provider class.
        """
        provider_class = ProviderType.registry.get(self.class_id)
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

    def fetch_catalog(self, db_session: orm.Session) -> None:
        """Fetch this provider's catalog and save it to storage and db."""
        try:
            logger.debug(
                "Fetching catalog of provider ...", extra={"provider_id": self.id}
            )
            with db_session.begin(), self.get_provider_instance() as provider_fetcher:
                new_catalog = Catalog(
                    provider_id=self.id,
                    valid_since=provider_fetcher.get_valid_since().astimezone(UTC),
                    valid_until=provider_fetcher.get_valid_until().astimezone(UTC),
                )
                db_session.add(new_catalog)
                db_session.flush()
                logger.debug(
                    "Success adding new catalog.",
                    extra={"provider_id": self.id, "catalog_id": new_catalog.id},
                )
                for (
                    page_number,
                    page_bytes,
                ) in provider_fetcher.iter_catalog_pages():
                    page_storage_path = provider_fetcher.get_new_storage_path()
                    page_storage_path.write_bytes(page_bytes)
                    logger.debug(
                        "Success saving page data to storage.",
                        extra={
                            "provider_id": self.id,
                            "catalog_id": new_catalog.id,
                            "page_nr": page_number,
                            "storage_path": page_storage_path,
                        },
                    )
                    new_page = Page(
                        catalog_id=new_catalog.id,
                        number=page_number,
                        storage_path=str(page_storage_path),
                    )
                    db_session.add(new_page)
        except ProviderBrokenWarning:
            logger.exception(
                "Provider reported as broken!",
                extra={
                    "provider_id": self.id,
                    "provider_class_id": self.class_id,
                },
            )
            self.is_broken = True
        except ProviderMisconfiguredWarning:
            logger.exception(
                "Provider reported as misconfigured!",
                extra={
                    "provider_id": self.id,
                },
            )
            self.is_misconfigured = True
        else:
            logger.debug(
                "Success fetching catalog of provider.",
                extra={"provider_id": self.id},
            )
            self.is_misconfigured = False
            self.is_broken = False
        db_session.commit()


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

    def as_pdf(self) -> bytes:
        """Compress the catalog to a pdf file.

        Returns:
            A BytesIO of the pdf file.
        """
        pdf_bytes_io = BytesIO()
        page_images = [Image.open(page.storage_path) for page in self.pages]
        page_images[0].save(
            pdf_bytes_io,
            format="PDF",
            resolution=100.0,
            save_all=True,
            append_images=page_images[1:],
        )
        pdf_bytes_io.seek(0)
        return pdf_bytes_io.read()

    @classmethod
    def cleanup(cls, db_session: orm.Session, deadline: datetime) -> None:
        """Cleanup catalogs created before a deadline.

        Args:
            db_session: A database session.
            deadline: The deadline for catalog deletion.
        """
        logger.info(
            "Deleting outdated catalogs ...",
            extra={"expiration_deadline": deadline},
        )
        for catalog in db_session.query(cls).filter(cls.created_at < deadline).all():
            with db_session.begin():
                db_session.delete(catalog)
            logger.debug(
                "Deleted outdated catalog.",
                extra={
                    "catalog_id": catalog.id,
                    "creation_date": catalog.created_at,
                    "expiration_deadline": deadline,
                },
            )
        logger.info(
            "Success deleting outdated catalogs.",
            extra={"expiration_deadline": deadline},
        )


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
    with contextlib.suppress(FileNotFoundError):
        os.remove(target.storage_path)
    logger.debug(
        "Success cleaning up page file of a deleted page.",
        extra={"page_id": target.id, "page_storage_path": target.storage_path},
    )


@event.listens_for(Provider, "after_insert")
def after_provider_insert(
    mapper: orm.Mapper,  # noqa: ARG001  # required for event decorator
    connection: Connection,
    target: Provider,
) -> None:
    """Event setting up a providers task after its insertion."""
    provider_class = ProviderType.registry.get(target.class_id)
    if not provider_class:
        logger.error(
            "No provider class found for newly inserted provider instance!",
            extra={"provider_id": target.id, "provider_class_id": target.class_id},
        )
        return
    with orm.Session(bind=connection) as db_session:
        crontab = CrontabSchedule.from_schedule(db_session, provider_class.schedule)
        task = PeriodicTask(
            name=f"{target.class_id}-{target.config}",
            task="cata_log.tasks.fetch_provider",
            args=f"[{target.id}]",
            crontab_id=crontab.id,
            enabled=True,
        )
        db_session.add(task)
        db_session.flush()
        db_session.execute(
            Provider.__table__.update()
            .where(Provider.id == target.id)
            .values(task_id=task.id)
        )
    logger.debug(
        "Success adding periodictask to a newly inserted provider.",
        extra={"provider_id": target.id, "task_id": target.task_id},
    )


@event.listens_for(Provider, "before_delete")
def before_provider_delete(
    mapper: orm.Mapper,  # noqa: ARG001  # required for event decorator
    connection: Connection,
    target: Provider,
) -> None:
    """Event cleaning up a providers task before deleting the provider."""
    connection.execute(delete(PeriodicTask).where(PeriodicTask.id == target.task_id))
    logger.debug(
        "Success cleaning up periodictask of a deleted provider.",
        extra={"provider_id": target.id, "task_id": target.task_id},
    )
