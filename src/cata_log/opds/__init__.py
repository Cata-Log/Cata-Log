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

from fastapi import Response, status
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session, selectinload

from cata_log import database

from .utils import AcquisitionLink, Entry, Metadata, OPDSCatalog, ThumbnailLink

router = APIRouter(prefix="/opds", tags=["opds"])

__all__ = ["router"]


@router.get("/")
def get_opds_catalog_overview(
    db_session: Session = database.depends_db_session,
) -> Response:
    """Get the odps overview."""
    catalogs = (
        db_session.query(database.Catalog)
        .options(
            selectinload(database.Catalog.provider),
            selectinload(database.Catalog.pages),
        )
        .order_by(database.Catalog.created_at.desc())
        .all()
    )
    opds = OPDSCatalog(title="Cata-Log Library")
    for catalog in catalogs:
        provider_class = catalog.provider.get_provider_class()
        entry = Entry(
            title=f"{catalog.provider.class_id.title()} {catalog.valid_since.date()} - {catalog.valid_until.date()}",
            uid=str(catalog.id),
        )
        entry.metadata.extend(
            [
                Metadata(provider_class.description, "summary"),
                Metadata(provider_class.region.language_code, "language", "dc"),
                Metadata(catalog.provider.class_id.title(), "publisher", "dc"),
                Metadata(catalog.created_at.date().isoformat(), "issued", "dc"),
                Metadata(
                    catalog.updated_at.isoformat(timespec="seconds"), "updated", "dc"
                ),
            ]
        )
        entry.links.extend(
            [
                ThumbnailLink(
                    href="/api/v1/pages/{catalog.pages[0].id}/download",
                    type=catalog.pages[0].media_type,
                ),
                AcquisitionLink(
                    href=f"/api/v1/pages/{catalog.pages[0].id}/download",
                    type="application/pdf",
                ),
                AcquisitionLink(
                    href=f"/odps{catalog.id}.epub",
                    type="application/epub+zip",
                ),
            ]
        )
        opds.entries.append(entry)
    return Response(content=opds.write(), media_type="application/atom+xml")


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
