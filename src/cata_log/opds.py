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
from urllib.parse import urljoin

import opds
from fastapi import Response, status
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.routing import APIRouter
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from cata_log import database

router = APIRouter(prefix="/opds", tags=["opds"], include_in_schema=False)

__all__ = ["router"]


@router.get("/")
def get_opds_catalog_overview(request: Request) -> Response:
    """Get the odps overview."""
    opds_catalog = opds.OPDSCatalog(title="Cata-Log Library")
    author = opds.Author()
    author.metadata.extend(
        [
            opds.Metadata(name="name", value="Cata-Log"),
            opds.Metadata(
                name="uri", value=urljoin(request.url.scheme, request.url.netloc)
            ),
        ]
    )
    opds_catalog.metadata.append(author)
    opds_catalog.links.extend(
        [
            opds.NavigationFeedLink(href="/opds/", rel=opds.Link.Rel.START),
            opds.NavigationFeedLink(href="/opds/", rel=opds.Link.Rel.SELF),
        ]
    )
    latest_entry = opds.Entry(title="Latest", uid="latest")
    latest_entry.links.append(
        opds.AcquistionFeedLink(href="/opds/latest/", rel=opds.Link.Rel.SORT_NEW)
    )
    all_entry = opds.Entry(title="All", uid="all")
    all_entry.links.append(
        opds.AcquistionFeedLink(href="/opds/all/", rel=opds.Link.Rel.SUBSECTION)
    )
    current_entry = opds.Entry(title="Current", uid="current")
    current_entry.links.append(
        opds.AcquistionFeedLink(href="/opds/current/", rel=opds.Link.Rel.SUBSECTION)
    )
    previews_entry = opds.Entry(title="Previews", uid="latest")
    previews_entry.links.append(
        opds.AcquistionFeedLink(href="/opds/previews/", rel=opds.Link.Rel.SUBSECTION)
    )
    outdated_entry = opds.Entry(title="Outdated", uid="outdated")
    outdated_entry.links.append(
        opds.AcquistionFeedLink(href="/opds/outdated/", rel=opds.Link.Rel.SUBSECTION)
    )
    providers_entry = opds.Entry(title="Provider Overview", uid="latest")
    providers_entry.links.append(
        opds.NavigationFeedLink(href="/opds/providers/", rel=opds.Link.Rel.SUBSECTION)
    )
    opds_catalog.entries.extend(
        [
            latest_entry,
            all_entry,
            current_entry,
            previews_entry,
            outdated_entry,
            providers_entry,
        ]
    )
    return Response(content=opds_catalog.write(), media_type="application/atom+xml")


@router.get("/latest/")
def get_opds_catalog_latest(
    request: Request,
    db_session: Session = database.depends_db_session,
) -> Response:
    """Get the latest catalog entries."""
    subquery = db_session.query(
        database.Catalog.id.label("id"),
        func.row_number()
        .over(
            partition_by=database.Catalog.provider_id,
            order_by=database.Catalog.created_at.desc(),
        )
        .label("rn"),
    ).subquery()
    catalogs = (
        db_session.query(database.Catalog)
        .join(subquery, database.Catalog.id == subquery.c.id)
        .filter(subquery.c.rn == 1)
        .all()
    )
    opds_catalog = opds.OPDSCatalog(title="Latest Catalogs")
    author = opds.Author()
    author.metadata.extend(
        [
            opds.Metadata(name="name", value="Cata-Log"),
            opds.Metadata(
                name="uri", value=urljoin(request.url.scheme, request.url.netloc)
            ),
        ]
    )
    opds_catalog.metadata.append(author)
    opds_catalog.links.extend(
        [
            opds.NavigationFeedLink(href="/opds/", rel=opds.Link.Rel.START),
            opds.AcquistionFeedLink(href="/opds/latest/", rel=opds.Link.Rel.SELF),
        ]
    )
    for catalog in catalogs:
        opds_catalog.entries.append(catalog.as_opds_entry())
    return Response(content=opds_catalog.write(), media_type="application/atom+xml")


@router.get("/all/")
def get_opds_catalog_all(
    request: Request,
    db_session: Session = database.depends_db_session,
) -> Response:
    """Get the preview catalog entries."""
    catalogs = (
        db_session.query(database.Catalog)
        .order_by(database.Catalog.created_at.desc())
        .options(selectinload(database.Catalog.provider))
        .all()
    )
    opds_catalog = opds.OPDSCatalog(title="All Catalogs")
    author = opds.Author()
    author.metadata.extend(
        [
            opds.Metadata(name="name", value="Cata-Log"),
            opds.Metadata(
                name="uri", value=urljoin(request.url.scheme, request.url.netloc)
            ),
        ]
    )
    opds_catalog.metadata.append(author)
    opds_catalog.links.extend(
        [
            opds.NavigationFeedLink(href="/opds/", rel=opds.Link.Rel.START),
            opds.AcquistionFeedLink(href="/opds/all/", rel=opds.Link.Rel.SELF),
        ]
    )
    for catalog in catalogs:
        opds_catalog.entries.append(catalog.as_opds_entry())
    return Response(content=opds_catalog.write(), media_type="application/atom+xml")


@router.get("/previews/")
def get_opds_catalog_previews(
    request: Request,
    db_session: Session = database.depends_db_session,
) -> Response:
    """Get the preview catalog entries."""
    catalogs = (
        db_session.query(database.Catalog)
        .filter(database.Catalog.valid_since >= datetime.now(tz=UTC))
        .order_by(database.Catalog.created_at.desc())
        .options(selectinload(database.Catalog.provider))
        .all()
    )
    opds_catalog = opds.OPDSCatalog(title="Preview Catalogs")
    author = opds.Author()
    author.metadata.extend(
        [
            opds.Metadata(name="name", value="Cata-Log"),
            opds.Metadata(
                name="uri", value=urljoin(request.url.scheme, request.url.netloc)
            ),
        ]
    )
    opds_catalog.metadata.append(author)
    opds_catalog.links.extend(
        [
            opds.NavigationFeedLink(href="/opds/", rel=opds.Link.Rel.START),
            opds.AcquistionFeedLink(href="/opds/previews/", rel=opds.Link.Rel.SELF),
        ]
    )
    for catalog in catalogs:
        opds_catalog.entries.append(catalog.as_opds_entry())
    return Response(content=opds_catalog.write(), media_type="application/atom+xml")


@router.get("/outdated/")
def get_opds_catalog_outdated(
    request: Request,
    db_session: Session = database.depends_db_session,
) -> Response:
    """Get the outdated catalog entries."""
    catalogs = (
        db_session.query(database.Catalog)
        .filter(database.Catalog.valid_until < datetime.now(tz=UTC))
        .order_by(database.Catalog.created_at.desc())
        .options(selectinload(database.Catalog.provider))
        .all()
    )
    opds_catalog = opds.OPDSCatalog(title="Outdated Catalogs")
    author = opds.Author()
    author.metadata.extend(
        [
            opds.Metadata(name="name", value="Cata-Log"),
            opds.Metadata(
                name="uri", value=urljoin(request.url.scheme, request.url.netloc)
            ),
        ]
    )
    opds_catalog.metadata.append(author)
    opds_catalog.links.extend(
        [
            opds.NavigationFeedLink(href="/opds/", rel=opds.Link.Rel.START),
            opds.AcquistionFeedLink(href="/opds/outdated/", rel=opds.Link.Rel.SELF),
        ]
    )
    for catalog in catalogs:
        opds_catalog.entries.append(catalog.as_opds_entry())
    return Response(content=opds_catalog.write(), media_type="application/atom+xml")


@router.get("/current/")
def get_opds_catalog_current(
    request: Request,
    db_session: Session = database.depends_db_session,
) -> Response:
    """Get the current catalog entries."""
    now = datetime.now(tz=UTC)
    catalogs = (
        db_session.query(database.Catalog)
        .filter(database.Catalog.valid_since <= now)
        .filter(database.Catalog.valid_until > now)
        .order_by(database.Catalog.created_at.desc())
        .options(selectinload(database.Catalog.provider))
        .all()
    )
    opds_catalog = opds.OPDSCatalog(title="Current Catalogs")
    author = opds.Author()
    author.metadata.extend(
        [
            opds.Metadata(name="name", value="Cata-Log"),
            opds.Metadata(
                name="uri", value=urljoin(request.url.scheme, request.url.netloc)
            ),
        ]
    )
    opds_catalog.metadata.append(author)
    opds_catalog.links.extend(
        [
            opds.NavigationFeedLink(href="/opds/", rel=opds.Link.Rel.START),
            opds.AcquistionFeedLink(href="/opds/current/", rel=opds.Link.Rel.SELF),
        ]
    )
    for catalog in catalogs:
        opds_catalog.entries.append(catalog.as_opds_entry())
    return Response(content=opds_catalog.write(), media_type="application/atom+xml")


@router.get("/providers/")
def get_opds_catalog_providers(
    request: Request,
    db_session: Session = database.depends_db_session,
) -> Response:
    """Get the provider entries."""
    providers = (
        db_session.query(database.Provider).order_by(database.Provider.class_uid).all()
    )
    opds_catalog = opds.OPDSCatalog(title="Catalog Providers Library")
    author = opds.Author()
    author.metadata.extend(
        [
            opds.Metadata(name="name", value="Cata-Log"),
            opds.Metadata(
                name="uri", value=urljoin(request.url.scheme, request.url.netloc)
            ),
        ]
    )
    opds_catalog.metadata.append(author)
    opds_catalog.links.extend(
        [
            opds.NavigationFeedLink(href="/opds/", rel=opds.Link.Rel.START),
            opds.NavigationFeedLink(href="/opds/providers/", rel=opds.Link.Rel.SELF),
        ]
    )
    for provider in providers:
        entry = opds.Entry(title=provider.class_uid.title(), uid=str(provider.id))
        entry.links.append(
            opds.AcquistionFeedLink(
                href=f"/opds/providers/{provider.id}/", rel=opds.Link.Rel.SUBSECTION
            )
        )
        opds_catalog.entries.append(entry)
    return Response(content=opds_catalog.write(), media_type="application/atom+xml")


@router.get("/providers/{provider_id}/")
def get_opds_catalog_provider(
    request: Request,
    provider_id: int,
    db_session: Session = database.depends_db_session,
) -> Response:
    """Get a provider's catalog entries."""
    catalogs = (
        db_session.query(database.Catalog)
        .options(selectinload(database.Catalog.provider))
        .filter(database.Catalog.provider_id == provider_id)
        .order_by(database.Catalog.created_at.desc())
        .all()
    )
    opds_catalog = opds.OPDSCatalog(title="Provider Catalogs")
    author = opds.Author()
    author.metadata.extend(
        [
            opds.Metadata(name="name", value="Cata-Log"),
            opds.Metadata(
                name="uri", value=urljoin(request.url.scheme, request.url.netloc)
            ),
        ]
    )
    opds_catalog.metadata.append(author)
    opds_catalog.links.extend(
        [
            opds.NavigationFeedLink(href="/opds/", rel=opds.Link.Rel.START),
            opds.NavigationFeedLink(href="/opds/providers/", rel=opds.Link.Rel.UP),
            opds.AcquistionFeedLink(
                href=f"/opds/providers/{provider_id}/", rel=opds.Link.Rel.SELF
            ),
        ]
    )
    for catalog in catalogs:
        opds_catalog.entries.append(catalog.as_opds_entry())
    return Response(content=opds_catalog.write(), media_type="application/atom+xml")


@router.get("/{catalog_id}.epub")
def get_catalog_epub(
    catalog_id: int, db_session: Session = database.depends_db_session
) -> Response:
    """Get a single catalog as epub."""
    catalog = db_session.get(
        database.Catalog,
        catalog_id,
        options=[
            selectinload(database.Catalog.pages),
            selectinload(database.Catalog.provider),
        ],
    )
    if not catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog not found"
        )
    return Response(
        content=catalog.as_epub(),
        media_type="application/epub+zip",
        headers={"Content-Disposition": f'attachment; filename="{catalog_id}.epub"'},
    )
