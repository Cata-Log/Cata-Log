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
import mimetypes
import uuid
from datetime import UTC, datetime
from functools import cached_property
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import opds
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger
from ebooklib import epub
from PIL import Image
from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    orm,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import select

from cata_log.constants import StatusEnum
from cata_log.exceptions import (
    NetworkError,
    ProviderUnknownClassWarning,
    ProviderWarning,
)
from cata_log.providers import Provider as ProviderType
from cata_log.scheduler import scheduler
from cata_log.settings import settings

from .mixins import TimestampMixin
from .types import PathType

logger = logging.getLogger(__name__)


class ModelBase(DeclarativeBase):
    """Base for all ORM models."""


class Provider(ModelBase, TimestampMixin):
    """ORM model for a catalog provider."""

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    class_uid: orm.Mapped[str] = orm.mapped_column()
    configuration: orm.Mapped[dict[str, str]] = orm.mapped_column(JSON)
    note: orm.Mapped[str] = orm.mapped_column(default="")
    job_id: orm.Mapped[int | None] = orm.mapped_column(nullable=True, unique=True)
    catalogs: orm.Mapped[list[Catalog]] = orm.relationship(
        back_populates="provider", cascade="all, delete-orphan"
    )
    status: orm.Mapped[StatusEnum] = orm.mapped_column(
        SQLEnum(StatusEnum, name="provider_status_enum"),
        default=StatusEnum.HEALTHY,
        server_default=StatusEnum.HEALTHY.value,
    )
    __tablename__ = "providers"
    __table_args__ = (UniqueConstraint("class_uid", "configuration"),)

    def get_provider_class(self) -> type[ProviderType]:
        """Get the class for this provider.

        Returns:
            The provider class.
        """
        return ProviderType.get_class(self.class_uid)

    def get_provider_instance(self) -> ProviderType:
        """Get a class instance for this provider.

        Returns:
            The provider instance.
        """
        return self.get_provider_class()(self.configuration)

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
                    pagefile = PageFile.get_or_create(
                        db_session=db_session,
                        page_bytes=page_bytes,
                    )
                    logger.debug(
                        "Success saving page data to storage.",
                        extra={
                            "provider_id": self.id,
                            "catalog_id": new_catalog.id,
                            "page_nr": page_number,
                            "path": pagefile.path,
                        },
                    )
                    new_page = Page(
                        catalog_id=new_catalog.id,
                        file_id=pagefile.id,
                        number=page_number,
                    )
                    db_session.add(new_page)
        except ProviderWarning as provider_warning:
            logger.exception(
                "Provider catalog is %s!",
                provider_warning.provider_status.value,
                extra={
                    "provider_id": self.id,
                    "provider_class_uid": self.class_uid,
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

    def add_job(self) -> None:
        """Add the job for this provider."""
        if not self.job_id:
            try:
                provider_class = self.get_provider_class()
            except ProviderUnknownClassWarning:
                logger.exception(
                    "No provider class found for newly inserted provider instance!",
                    extra={
                        "provider_id": self.id,
                        "provider_class_uid": self.class_uid,
                    },
                )
                return
            cron_trigger = CronTrigger.from_crontab(
                provider_class.schedule, timezone=provider_class.region.timezone
            )
            cron_trigger.jitter = provider_class.jitter
            job = scheduler.add_job(
                name=f"{self.class_uid}-{self.configuration}",
                func="cata_log.jobs:fetch_provider",
                args=[self.id],
                trigger=cron_trigger,
            )
            self.job_id = job.id

    def remove_job(self) -> None:
        """Remove the job of this provider."""
        if self.job_id:
            with contextlib.suppress(JobLookupError):
                scheduler.remove_job(self.job_id)
            self.job_id = None


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
            The pdf file bytes.
        """
        pdf_bytes_io = BytesIO()
        page_images = [Image.open(page.file.path) for page in self.pages]
        page_images[0].save(
            pdf_bytes_io,
            format="PDF",
            resolution=100.0,
            save_all=True,
            append_images=page_images[1:],
        )
        pdf_bytes_io.seek(0)
        return pdf_bytes_io.read()

    def as_opds_entry(self) -> opds.Entry:
        """Create an OPDS entry for this catalog.

        Returns:
            An OPDS entry instance with this catalogs metadata.
        """
        provider_class = self.provider.get_provider_class()
        entry = opds.Entry(
            title=f"{provider_class.name.title()} {self.valid_since.date()} - {self.valid_until.date()}",
            uid=str(self.id),
        )
        entry.metadata.extend(
            [
                opds.Metadata(provider_class.description, "summary"),
                opds.Metadata(provider_class.region.language_code, "language", "dc"),
                opds.Metadata(self.provider.class_uid.title(), "publisher", "dc"),
                opds.Metadata(self.created_at.date().isoformat(), "issued", "dc"),
                opds.Metadata(
                    self.updated_at.isoformat(timespec="seconds"), "updated", "dc"
                ),
            ]
        )
        entry.links.extend(
            [
                opds.AcquisitionLink(
                    href=f"/api/v1/catalogs/{self.id}/download",
                    media_type="application/pdf",
                ),
                opds.AcquisitionLink(
                    href=f"/odps/{self.id}.epub",
                    media_type="application/epub+zip",
                ),
                opds.Link(
                    href=f"/catalogs/{self.id}/",
                    media_type="text/html",
                    rel=opds.Link.Rel.ALTERNATE,
                ),
            ]
        )
        if self.pages:
            entry.links.append(
                opds.ThumbnailLink(
                    href=f"/api/v1/pages/{self.pages[0].id}/download",
                    media_type=self.pages[0].file.media_type,
                ),
            )
        return entry

    def as_epub(self) -> bytes:
        """Convert the catalog to a epub file.

        Returns:
            The epub file bytes.
        """
        provider_class = self.provider.get_provider_class()
        book = epub.EpubBook()
        book.set_title(
            f"{self.provider.class_uid.title()}, {self.valid_since.date()} - {self.valid_until.date()}"
        )
        book.set_direction("rtl" if provider_class.region.is_rtl else "ltr")
        book.set_language(provider_class.region.language_code)
        book.set_cover(
            f"cover_{self.pages[0].file.name}",
            self.pages[0].file.path.read_bytes(),
        )
        book.add_author("Cata-Log")
        book.add_metadata("DC", "description", provider_class.description)
        book.add_metadata(
            None,
            "meta",
            "",
            {"valid_since": self.valid_since.isoformat(timespec="seconds")},
        )
        book.add_metadata(
            None,
            "meta",
            "",
            {"valid_until": self.valid_until.isoformat(timespec="seconds")},
        )
        for page in self.pages:
            page_image = epub.EpubImage(
                uid=str(page.id),
                file_name=page.file.name,
                content=page.file.path.read_bytes(),
            )
            book.add_item(page_image)
            page_chapter = epub.EpubHtml(
                title=f"Page {page.number + 1}",
                file_name=f"chap_{page.number + 1}.xhtml",
                content=f'<img src="{page.file.name}"/>',
            )
            book.add_item(page_chapter)
            book.spine.append(page_chapter)
        book.toc = book.spine
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        book_bytes_io = BytesIO()
        epub.write_epub(book_bytes_io, book)
        book_bytes_io.seek(0)
        return book_bytes_io.read()

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


class PageFile(ModelBase, TimestampMixin):
    """ORM model for a catalog page file."""

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    path: orm.Mapped[Path] = orm.mapped_column(PathType, unique=True)
    sha256: orm.Mapped[str] = orm.mapped_column()
    size: orm.Mapped[int] = orm.mapped_column()
    pages: orm.Mapped[list[Page]] = orm.relationship(
        back_populates="file",
        passive_deletes="all",  # essential to make ondelete=RESTRICT work: https://stackoverflow.com/questions/55968951/sqlalchemy-fk-ondelete-does-not-restrict
    )
    __tablename__ = "pagefiles"

    @property
    def name(self) -> str:
        """The name of the stored file."""
        return self.path.name

    @cached_property
    def media_type(self) -> str:
        """The mimetype of the stored file."""
        return (
            mimetypes.guess_file_type(self.name, strict=False)[0]
            or "application/octet-stream"
        )

    @classmethod
    def get_or_create(cls, db_session: orm.Session, page_bytes: bytes) -> PageFile:
        """Get or create a pagefile.

        Args:
            db_session: A database session to use.
            page_bytes: The content of the pagefile.
            path: The path for the pagefile.
        """
        sha256_hash = sha256(page_bytes).hexdigest()
        pagefile = db_session.query(cls).filter(cls.sha256 == sha256_hash).first()
        if not pagefile:
            pagefile = cls(sha256=sha256_hash, size=len(page_bytes))
            with Image.open(BytesIO(page_bytes)) as image:
                pagefile.set_new_path(
                    extension=mimetypes.guess_extension(
                        image.get_format_mimetype() or "", strict=False
                    )
                    or ""
                )
            db_session.add(pagefile)
            db_session.flush()
            pagefile.path.write_bytes(page_bytes)
        return pagefile

    def set_new_path(self, extension: str) -> None:
        """Set a new path.

        Args:
            extension: The extension of the filepath.
        """
        filename = str(uuid.uuid4()) + extension
        self.path = settings.storage_path / filename

    @classmethod
    def cleanup(cls, db_session: orm.Session) -> None:
        """Cleanup unused page files.

        Args:
            db_session: A database session.
        """
        used_paths = set(db_session.execute(select(cls.path)).scalars().all())
        for storage_filepath in settings.storage_path.iterdir():
            if storage_filepath.is_dir() or storage_filepath.resolve() in used_paths:
                continue
            storage_filepath.unlink(missing_ok=True)


class Page(ModelBase, TimestampMixin):
    """ORM model for a catalog page."""

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    number: orm.Mapped[int] = orm.mapped_column()
    catalog_id: orm.Mapped[int] = orm.mapped_column(
        ForeignKey(Catalog.__tablename__ + ".id", ondelete="CASCADE"), nullable=False
    )
    catalog: orm.Mapped[Catalog] = orm.relationship(back_populates="pages")
    file_id: orm.Mapped[int] = orm.mapped_column(
        ForeignKey(PageFile.__tablename__ + ".id", ondelete="RESTRICT"), nullable=False
    )
    file: orm.Mapped[PageFile] = orm.relationship(back_populates="pages")

    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("catalog_id", "number"),)
