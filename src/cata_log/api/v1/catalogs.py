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

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.responses import FileResponse, Response
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import AwareDatetime, BaseModel
from pydantic.types import NonNegativeInt
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import func

from cata_log import database
from cata_log.api import common
from cata_log.api.mixins import AwareTimestampsMixin
from cata_log.utils.queries import order_sql

from .pages import Page
from .pagination import PaginationPage

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


class Catalog(AwareTimestampsMixin, BaseModel):
    """Catalog data model."""

    id: int
    provider_id: int
    valid_since: AwareDatetime
    valid_until: AwareDatetime


class FullCatalog(Catalog):
    """Full catalog data model."""

    pages: list[Page]


@router.get("", response_model=PaginationPage[Catalog], operation_id="list-catalogs-v1")
def list_catalogs(
    order: Annotated[list[str], Query(description="Field names to order by")] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        "-created_at"
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Catalog]:
    """List all catalogs."""
    return paginate(
        db_session.query(database.Catalog)
        .options(selectinload(database.Catalog.pages))
        .order_by(*[order_sql(order_param) for order_param in order])
    )


@router.get(
    "/latest",
    response_model=PaginationPage[Catalog],
    operation_id="list-latest-catalogs-v1",
)
def list_latest_catalogs(
    order: Annotated[list[str], Query(description="Field names to order by")] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        "-created_at"
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Catalog]:
    """List the latest catalog for every provider."""
    subquery = db_session.query(
        database.Catalog.id.label("id"),
        func.row_number()
        .over(
            partition_by=database.Catalog.provider_id,
            order_by=database.Catalog.created_at.desc(),
        )
        .label("rn"),
    ).subquery()
    return paginate(
        db_session.query(database.Catalog)
        .join(subquery, database.Catalog.id == subquery.c.id)
        .filter(subquery.c.rn == 1)
        .order_by(*[order_sql(order_param) for order_param in order])
    )


@router.get(
    "/previews",
    response_model=PaginationPage[Catalog],
    operation_id="list-preview-catalogs-v1",
)
def list_previews_catalogs(
    order: Annotated[list[str], Query(description="Field names to order by")] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        "-created_at"
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Catalog]:
    """List all preview catalogs."""
    return paginate(
        db_session.query(database.Catalog)
        .filter(database.Catalog.valid_since >= datetime.now(tz=UTC))
        .options(selectinload(database.Catalog.pages))
        .order_by(*[order_sql(order_param) for order_param in order])
    )


@router.get(
    "/current",
    response_model=PaginationPage[Catalog],
    operation_id="list-current-catalogs-v1",
)
def list_current_catalogs(
    order: Annotated[list[str], Query(description="Field names to order by")] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        "-created_at"
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Catalog]:
    """List all current catalogs."""
    now = datetime.now(tz=UTC)
    return paginate(
        db_session.query(database.Catalog)
        .filter(database.Catalog.valid_since <= now)
        .filter(database.Catalog.valid_until > now)
        .options(selectinload(database.Catalog.pages))
        .order_by(*[order_sql(order_param) for order_param in order])
    )


@router.get(
    "/outdated",
    response_model=PaginationPage[Catalog],
    operation_id="list-outdated-catalogs-v1",
)
def list_outdated_catalogs(
    order: Annotated[list[str], Query(description="Field names to order by")] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        "-created_at"
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Catalog]:
    """List all outdated catalogs."""
    return paginate(
        db_session.query(database.Catalog)
        .filter(database.Catalog.valid_until < datetime.now(tz=UTC))
        .options(selectinload(database.Catalog.pages))
        .order_by(*[order_sql(order_param) for order_param in order])
    )


@router.get(
    "/{catalog_id}",
    response_model=FullCatalog,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    operation_id="get-catalog-v1",
)
def get_catalog(
    catalog_id: Annotated[int, Path(description="ID of the catalog")],
    db_session: Session = database.depends_db_session,
) -> database.Catalog:
    """Get a single catalog."""
    catalog = db_session.get(
        database.Catalog, catalog_id, options=[selectinload(database.Catalog.pages)]
    )
    if not catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog not found"
        )
    return catalog


@router.get(
    "/{catalog_id}/download",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    operation_id="download-catalog-v1",
)
def download_catalog(
    catalog_id: Annotated[int, Path(description="ID of the catalog")],
    filename: Annotated[str | None, Query(description="Name for the file")] = None,
    db_session: Session = database.depends_db_session,
) -> Response:
    """Download a catalog as pdf."""
    catalog = db_session.get(
        database.Catalog, catalog_id, options=[selectinload(database.Catalog.pages)]
    )
    if not catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog not found"
        )
    filename = filename or f"catalog-{catalog.id}.pdf"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
    }
    return Response(catalog.as_pdf(), headers=headers, media_type="application/pdf")


@router.get(
    "/{catalog_id}/embed",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    operation_id="embed-catalog-v1",
)
def embed_catalog(
    catalog_id: Annotated[int, Path(description="ID of the catalog")],
    filename: Annotated[str | None, Query(description="Name for the file")] = None,
    db_session: Session = database.depends_db_session,
) -> Response:
    """Embed a catalog as pdf."""
    catalog = db_session.get(
        database.Catalog, catalog_id, options=[selectinload(database.Catalog.pages)]
    )
    if not catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog not found"
        )
    filename = filename or f"catalog-{catalog.id}.pdf"
    headers = {
        "Content-Disposition": f"inline; filename={filename}",
    }
    return Response(
        catalog.as_pdf(),
        headers=headers,
        media_type="application/pdf",
    )


@router.get(
    "/{catalog_id}/pages",
    response_model=PaginationPage[Page],
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    operation_id="get-catalog-pages-v1",
)
def get_catalog_pages(
    catalog_id: Annotated[int, Path(description="ID of the catalog")],
    order: Annotated[list[str], Query(description="Field names to order by")] = [  # noqa: B006 # no alternative in fastapi, not altered after declaration
        "number"
    ],
    db_session: Session = database.depends_db_session,
) -> PaginationPage[database.Page]:
    """Get catalog pages."""
    return paginate(
        db_session.query(database.Page)
        .filter(database.Page.catalog_id == catalog_id)
        .order_by(*[order_sql(order_param) for order_param in order])
    )


@router.get(
    "/{catalog_id}/pages/{page_number}",
    response_model=Page,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    operation_id="get-catalog-page-v1",
)
def get_catalog_page(
    catalog_id: Annotated[int, Path(description="ID of the catalog")],
    page_number: Annotated[NonNegativeInt, Path(description="Number of the page")],
    db_session: Session = database.depends_db_session,
) -> database.Page:
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


@router.get(
    "/{catalog_id}/pages/{page_number}/download",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    operation_id="download-catalog-page-v1",
)
def download_catalog_page(
    catalog_id: Annotated[int, Path(description="ID of the catalog")],
    page_number: Annotated[NonNegativeInt, Path(description="Number of the page")],
    filename: str | None = None,
    db_session: Session = database.depends_db_session,
) -> FileResponse:
    """Download a single catalog page by its page number."""
    page_path = (
        db_session.query(database.PageFile.path)
        .join(database.Page.file)
        .filter(database.Page.catalog_id == catalog_id)
        .filter(database.Page.number == page_number)
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
    "/{catalog_id}/pages/{page_number}/embed",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": common.HTTPStatusError,
            "description": "Object doesn't exist",
        },
    },
    operation_id="embed-catalog-page-v1",
)
def embed_catalog_page(
    catalog_id: Annotated[int, Path(description="ID of the catalog")],
    page_number: Annotated[NonNegativeInt, Path(description="Number of the page")],
    filename: Annotated[str | None, Query(description="Name for the file")] = None,
    db_session: Session = database.depends_db_session,
) -> FileResponse:
    """Embed a single catalog page by its page number."""
    page_path = (
        db_session.query(database.PageFile.path)
        .join(database.Page.file)
        .filter(database.Page.catalog_id == catalog_id)
        .filter(database.Page.number == page_number)
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
