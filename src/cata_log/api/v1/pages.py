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

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, computed_field
from sqlalchemy.orm import Session

from cata_log import database
from cata_log.api.mixins import TimestampMixin

router = APIRouter(prefix="/pages", tags=["pages"])


class Page(BaseModel, TimestampMixin):
    """Page data model."""

    id: int
    number: int
    catalog_id: int
    storage_path: str

    @computed_field
    @property
    def static_filename(self) -> str:
        """Compute the static filename from the storage path."""
        return Path(self.storage_path).name


@router.get("", response_model=list[Page])
async def list_pages(
    db_session: Session = database.depends_db_session,
) -> list[database.Page]:
    """List all pages."""
    return (
        db_session.query(database.Page)
        .order_by(database.Page.catalog_id, database.Page.number)
        .all()
    )


@router.get("/{page_id}", response_model=Page)
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


@router.get("/{page_id}/download")
async def download_page(
    page_id: int,
    filename: str | None = None,
    db_session: Session = database.depends_db_session,
) -> FileResponse:
    """Download a single page."""
    page = db_session.get(database.Page, page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    file_path = page.storage_path
    filename = filename or os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        filename=filename,
        content_disposition_type="attachment",
    )


@router.get("/{page_id}/embed")
async def embed_page(
    page_id: int,
    filename: str | None = None,
    db_session: Session = database.depends_db_session,
) -> FileResponse:
    """Embed a single page."""
    page = db_session.get(database.Page, page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    file_path = page.storage_path
    filename = filename or os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        filename=filename,
        content_disposition_type="inline",
    )
