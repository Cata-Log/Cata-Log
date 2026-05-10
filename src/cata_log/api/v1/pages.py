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


from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from cata_log import database
from cata_log.api import common
from cata_log.api.mixins import AwareTimestampsMixin

router = APIRouter(prefix="/pages", tags=["pages"])


class PageFile(AwareTimestampsMixin, BaseModel):
    """Page file data model."""

    id: int
    sha256: str
    size: int
    width: int
    height: int
    name: str


class Page(AwareTimestampsMixin, BaseModel):
    """Page data model."""

    id: int
    number: int
    catalog_id: int
    file: PageFile


@router.get(
    "",
    response_model=list[Page],
    operation_id="list-pages-v1",
)
def list_pages(
    db_session: Session = database.depends_db_session,
) -> list[database.Page]:
    """List all pages."""
    return (
        db_session.query(database.Page)
        .join(database.Catalog, database.Page.catalog_id == database.Catalog.id)
        .order_by(database.Catalog.created_at.desc(), database.Page.number)
        .all()
    )


@router.get(
    "/{page_id}",
    response_model=Page,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist.",
        },
    },
    operation_id="get-page-v1",
)
def get_page(
    page_id: int, db_session: Session = database.depends_db_session
) -> database.Page:
    """Get a single page."""
    page = db_session.get(database.Page, page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    return page


@router.get(
    "/{page_id}/download",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist.",
        },
    },
    operation_id="download-page-v1",
)
def download_page(
    page_id: int,
    filename: str | None = None,
    db_session: Session = database.depends_db_session,
) -> FileResponse:
    """Download a single page."""
    page_path = (
        db_session.query(database.PageFile.path)
        .join(database.Page.file)
        .filter(database.Page.id == page_id)
        .scalar()
    )
    if not page_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    filename = filename or page_path.name
    return FileResponse(
        path=page_path,
        filename=filename,
        content_disposition_type="attachment",
    )


@router.get(
    "/{page_id}/embed",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist.",
        },
    },
    operation_id="embed-page-v1",
)
def embed_page(
    page_id: int,
    filename: str | None = None,
    db_session: Session = database.depends_db_session,
) -> FileResponse:
    """Embed a single page."""
    page_path = (
        db_session.query(database.PageFile.path)
        .join(database.Page.file)
        .filter(database.Page.id == page_id)
        .scalar()
    )
    if not page_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    filename = filename or page_path.name
    return FileResponse(
        path=page_path,
        filename=filename,
        content_disposition_type="inline",
    )
