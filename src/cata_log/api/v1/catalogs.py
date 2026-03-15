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
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from cata_log import database

from .pages import Page

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


class Catalog(BaseModel):
    """Catalog data model."""

    id: int
    provider_id: int
    valid_since: datetime
    valid_until: datetime
    pages: list[Page]


@router.get("", response_model=list[Catalog])
async def list_catalogs(
    db_session: Session = database.depends_db_session,
) -> list[database.Catalog]:
    """List all catalogs."""
    return db_session.query(database.Catalog).all()


@router.get("/previews", response_model=list[Catalog])
async def list_previews_catalogs(
    db_session: Session = database.depends_db_session,
) -> list[database.Catalog]:
    """List all preview catalogs."""
    return (
        db_session.query(database.Catalog)
        .filter(database.Catalog.valid_since >= datetime.now(tz=UTC))
        .all()
    )


@router.get("/current", response_model=list[Catalog])
async def list_current_catalogs(
    db_session: Session = database.depends_db_session,
) -> list[database.Catalog]:
    """List all current catalogs."""
    now = datetime.now(tz=UTC)
    return (
        db_session.query(database.Catalog)
        .filter(database.Catalog.valid_since <= now)
        .filter(database.Catalog.valid_until > now)
        .all()
    )


@router.get("/outdated", response_model=list[Catalog])
async def list_outdated_catalogs(
    db_session: Session = database.depends_db_session,
) -> list[database.Catalog]:
    """List all outdated catalogs."""
    return (
        db_session.query(database.Catalog)
        .filter(database.Catalog.valid_until < datetime.now(tz=UTC))
        .all()
    )


@router.get("/{catalog_id}", response_model=Catalog)
async def get_catalog(
    catalog_id: int, db_session: Session = database.depends_db_session
) -> database.Catalog:
    """Get a single catalog."""
    catalog = db_session.get(database.Catalog, catalog_id)
    if not catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog not found"
        )
    return catalog


@router.get("/{catalog_id}/pages/{page_number}", response_model=Page)
async def get_catalog_page(
    catalog_id: int, page_number: int, db_session: Session = database.depends_db_session
) -> database.Catalog:
    """Get a single catalog page by its page number."""
    page = (
        db_session.query(database.Page)
        .filter(database.Page.catalog_id == catalog_id)
        .filter(database.Page.number == page_number)
        .first()
    )
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    return page


@router.get("/{catalog_id}/pages/{page_number}/download")
async def download_catalog_page(
    catalog_id: int,
    page_number: int,
    filename: str | None = None,
    db_session: Session = database.depends_db_session,
) -> FileResponse:
    """Download a single catalog page by its page number."""
    page = (
        db_session.query(database.Page)
        .filter(database.Page.catalog_id == catalog_id)
        .filter(database.Page.number == page_number)
        .one_or_none()
    )
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


@router.get("/{catalog_id}/pages/{page_number}/embed")
async def embed_catalog_page(
    catalog_id: int,
    page_number: int,
    filename: str | None = None,
    db_session: Session = database.depends_db_session,
) -> FileResponse:
    """Embed a single catalog page by its page number."""
    page = (
        db_session.query(database.Page)
        .filter(database.Page.catalog_id == catalog_id)
        .filter(database.Page.number == page_number)
        .one_or_none()
    )
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
