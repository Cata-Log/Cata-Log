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

import logging
from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO
from pathlib import Path

from celery_sqlalchemy_v2_scheduler.models import (
    ModelBase,
    PeriodicTask,
)
from PIL import Image
from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    orm,
)
from sqlalchemy import Enum as SQLEnum

from cata_log.constants import StatusEnum
from cata_log.exceptions import (
    NetworkError,
    ProviderWarning,
)
from cata_log.providers import Provider as ProviderType

from .mixins import TimestampMixin
from .types import PathType

logger = logging.getLogger(__name__)


class Provider(ModelBase, TimestampMixin):
    """ORM model for a catalog provider."""

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    class_id: orm.Mapped[str] = orm.mapped_column()
    config: orm.Mapped[dict[str, str]] = orm.mapped_column(JSON)
    task: orm.Mapped[PeriodicTask] = orm.relationship()
    task_id: orm.Mapped[int] = orm.mapped_column(
        ForeignKey(PeriodicTask.__tablename__ + ".id", ondelete="CASCADE"),
        nullable=True,
    )
    catalogs: orm.Mapped[list[Catalog]] = orm.relationship(
        back_populates="provider", cascade="all, delete-orphan"
    )
    status: orm.Mapped[StatusEnum] = orm.mapped_column(
        SQLEnum(StatusEnum, name="provider_status_enum"),
        default=StatusEnum.HEALTHY,
        server_default=StatusEnum.HEALTHY.value,
    )
    __tablename__ = "providers"
    __table_args__ = (UniqueConstraint("class_id", "config"),)

    def get_provider_class(self) -> type[ProviderType]:
        """Get the class for this provider.

        Returns:
            The provider class.
        """
        return ProviderType.get_class(self.class_id)

    def get_provider_instance(self) -> ProviderType:
        """Get a class instance for this provider.

        Returns:
            The provider instance.
        """
        return self.get_provider_class()(self.config)

    def fetch_catalog(self, db_session: orm.Session) -> None:
        """Fetch this provider's catalog and save it to storage and db."""
        try:
            logger.debug(
                "Fetching catalog of provider ...", extra={"provider_id": self.id}
            )
            with (
                db_session.begin_nested(),
                self.get_provider_instance() as provider_fetcher,
            ):
                db_session.add(self)
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
                        storage_path=page_storage_path,
                        sha256=sha256(page_bytes).hexdigest(),
                    )
                    db_session.add(new_page)
        except ProviderWarning as provider_warning:
            logger.exception(
                "Provider catalog is %s!",
                provider_warning.provider_status.value,
                extra={
                    "provider_id": self.id,
                    "provider_class_id": self.class_id,
                },
            )
            self.status = provider_warning.provider_status
        except NetworkError:
            logger.warning(
                "Network error while fetching provider catalog.",
                extra={
                    "provider_id": self.id,
                },
                exc_info=True,
            )
            raise
        else:
            logger.debug(
                "Success fetching catalog of provider.",
                extra={"provider_id": self.id},
            )
            self.status = StatusEnum.HEALTHY
        db_session.commit()

    @property
    def is_healthy(self) -> bool:
        """Shortcut property to check this providers health.

        Returns:
            Whether this provider is healthy.
        """
        return self.status in [
            StatusEnum.HEALTHY,
            StatusEnum.UNAVAILABLE,
        ]

    @property
    def is_misconfigured(self) -> bool:
        """Shortcut property to check this providers health.

        Returns:
            Whether this provider is or may be misconfigured.
        """
        return self.status in [
            StatusEnum.MISCONFIGURED,
            StatusEnum.MISCONFIGURED_OR_BROKEN,
        ]

    @property
    def is_broken(self) -> bool:
        """Shortcut property to check this providers health.

        Returns:
            Whether this provider is or may be broken.
        """
        return self.status in [
            StatusEnum.BROKEN,
            StatusEnum.MISCONFIGURED_OR_BROKEN,
        ]


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
            with db_session.begin_nested():
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
    storage_path: orm.Mapped[Path] = orm.mapped_column(PathType, unique=True)
    sha256: orm.Mapped[str] = orm.mapped_column()
    catalog: orm.Mapped[Catalog] = orm.relationship(back_populates="pages")
    catalog_id: orm.Mapped[int] = orm.mapped_column(
        ForeignKey(Catalog.__tablename__ + ".id", ondelete="CASCADE"), nullable=False
    )
    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("catalog_id", "number"),)
