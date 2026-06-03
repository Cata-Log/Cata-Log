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


from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.responses import FileResponse
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from cata_log_hub import database
from cata_log_hub.api import common

from . import models
from .pagination import PaginationPage

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get(
    "",
    response_model=PaginationPage[models.Page],
    operation_id="list-pages-v1",
)
def list_pages(
    order: Annotated[
        list[models.PageOrderChoices], Query(description="Fields to order by")
    ] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        models.PageOrderChoices.NUMBER,
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Page]:
    """List all pages."""
    return paginate(
        db_session.query(database.Page)
        .join(database.Catalog, database.Page.catalog_id == database.Catalog.id)
        .order_by(
            database.Catalog.created_at.desc(),
            *[order_param.sql for order_param in order],
        )
    )


@router.get(
    "/{page_id}",
    response_model=models.Page,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    operation_id="get-page-v1",
)
def get_page(
    page_id: Annotated[int, Path(description="ID of the page")],
    db_session: Session = database.depends_db_session,
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
            "description": "Object doesn't exist",
        },
    },
    operation_id="download-page-v1",
)
def download_page(
    page_id: Annotated[int, Path(title="test", description="ID of the page")],
    filename: Annotated[str | None, Query(description="Name for the file")] = None,
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
            "description": "Object doesn't exist",
        },
    },
    operation_id="embed-page-v1",
)
def embed_page(
    page_id: Annotated[int, Path(description="ID of the page")],
    filename: Annotated[str | None, Query(description="Name for the file")] = None,
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
