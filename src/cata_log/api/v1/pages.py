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

from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, computed_field, field_serializer
from sqlalchemy.orm import Session

from cata_log import database
from cata_log.api.mixins import TimestampMixin

router = APIRouter(prefix="/pages", tags=["pages"])


class Page(BaseModel, TimestampMixin):
    """Page data model."""

    id: int
    number: int
    catalog_id: int
    storage_path: Path

    model_config = ConfigDict(arbitrary_types_allowed=True)
    """Pydantic model configuration."""

    @field_serializer("storage_path")
    def serialize_storage_path(self, storage_path: Path) -> str:
        """Serialize storage_path.

        Args:
            storage_path: The Path instance to serialize.

        Returns:
            The str representation of the storage_path.
        """
        return str(storage_path)

    @computed_field  # type: ignore[prop-decorator]  # as documented for this decorator
    @property
    def static_filename(self) -> str:
        """Compute the static filename from the storage path."""
        return Path(self.storage_path).name


@router.get("", response_model=list[Page], operation_id="list-pages-v1")
async def list_pages(
    db_session: Session = database.depends_db_session,
) -> list[database.Page]:
    """List all pages."""
    return (
        db_session.query(database.Page)
        .join(database.Catalog, database.Page.catalog_id == database.Catalog.id)
        .order_by(database.Catalog.created_at.desc(), database.Page.number)
        .all()
    )


@router.get("/{page_id}", response_model=Page, operation_id="get-page-v1")
async def get_page(
    page_id: int, db_session: Session = database.depends_db_session
) -> database.Page:
    """Get a single page."""
    page = db_session.get(database.Page, page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    return page


@router.get("/{page_id}/download", operation_id="download-page-v1")
async def download_page(
    page_id: int,
    filename: str | None = None,
    db_session: Session = database.depends_db_session,
) -> FileResponse:
    """Download a single page."""
    page_storage_path = (
        db_session.query(database.Page.storage_path)
        .filter(database.Page.id == page_id)
        .scalar()
    )
    if not page_storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    filename = filename or page_storage_path.name
    return FileResponse(
        path=page_storage_path,
        filename=filename,
        content_disposition_type="attachment",
    )


@router.get("/{page_id}/embed", operation_id="embed-page-v1")
async def embed_page(
    page_id: int,
    filename: str | None = None,
    db_session: Session = database.depends_db_session,
) -> FileResponse:
    """Embed a single page."""
    page_storage_path = (
        db_session.query(database.Page.storage_path)
        .filter(database.Page.id == page_id)
        .scalar()
    )
    if not page_storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    filename = filename or page_storage_path.name
    return FileResponse(
        path=page_storage_path,
        filename=filename,
        content_disposition_type="inline",
    )
