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

from fastapi import APIRouter, HTTPException, responses, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from cata_log import database
from cata_log.providers import Provider as ProviderType
from cata_log.tasks import fetch_provider

from .catalogs import Catalog

router = APIRouter(prefix="/providers", tags=["providers"])


class Provider(BaseModel):
    """Provider data model."""

    id: int
    class_id: str
    config: dict[str, str]
    catalogs: list[Catalog]


class NewProvider(BaseModel):
    """Provider creation data model."""

    class_id: str
    config: dict[str, str]


class RegionInfo(BaseModel):
    """Region info data model."""

    local_name: str
    language_code: str
    timezone: str


class ProviderInfo(BaseModel):
    """Provider info data model."""

    id: str
    configuration: dict[str, str]
    description: str
    url: str
    region: RegionInfo


@router.get("", response_model=list[Provider])
async def list_providers(
    db_session: Session = database.depends_db_session,
) -> list[database.Provider]:
    """List all providers."""
    return db_session.query(database.Provider).all()


@router.get("/available", response_model=list[ProviderInfo])
async def list_available_providers(
    query: str | None = None, region: str | None = None
) -> list[dict[str, str | dict[str, str]]]:
    """List all available providers."""
    if region:
        region = region.lower()
    if query:
        query = query.lower()
    return [
        catalog_class.info()
        for catalog_class in ProviderType.registry.values()
        if (not query and not region)
        or (region and (region in catalog_class.region.local_name.lower()))
        or (
            query
            and (
                (query in catalog_class.id())
                or (query in catalog_class.description.lower())
            )
        )
    ]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Provider)
async def post_provider(
    new_provider: NewProvider, db_session: Session = database.depends_db_session
) -> database.Provider:
    """Set up a new provider."""
    provider_class = ProviderType.registry.get(new_provider.class_id)
    if not provider_class:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The given provider is unknown",
        )
    if any(
        not new_provider.config.get(config) for config in provider_class.configuration
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The given provider configuration is incomplete",
        )
    provider = database.Provider(**new_provider.model_dump())
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


@router.get("/{provider_id}", response_model=Provider)
async def get_provider(
    provider_id: int, db_session: Session = database.depends_db_session
) -> database.Provider:
    """Get a single provider."""
    provider = db_session.get(database.Provider, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    return provider


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: int, db_session: Session = database.depends_db_session
) -> None:
    """Delete a single provider. This also deletes all its catalogs and their pages."""
    provider = db_session.get(database.Provider, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    db_session.delete(provider)
    db_session.commit()


@router.get("/{provider_id}/catalogs", response_model=list[Catalog])
async def list_provider_catalogs(
    provider_id: int, db_session: Session = database.depends_db_session
) -> list[database.Catalog]:
    """List all catalogs of a provider."""
    return (
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .all()
    )


@router.get("/{provider_id}/catalogs/current", response_model=list[Catalog])
async def list_provider_current_catalogs(
    provider_id: int, db_session: Session = database.depends_db_session
) -> list[database.Catalog]:
    """List all current catalogs of a provider."""
    return (
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .filter(database.Catalog.valid_since <= datetime.now(tz=UTC))
        .filter(database.Catalog.valid_until > datetime.now(tz=UTC))
        .all()
    )


@router.get("/{provider_id}/catalogs/previews", response_model=list[Catalog])
async def list_provider_preview_catalogs(
    provider_id: int, db_session: Session = database.depends_db_session
) -> list[database.Catalog]:
    """List all preview catalogs of a provider."""
    return (
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .filter(database.Catalog.valid_since >= datetime.now(tz=UTC))
        .all()
    )


@router.get("/{provider_id}/catalogs/outdated", response_model=list[Catalog])
async def list_provider_outdated_catalogs(
    provider_id: int, db_session: Session = database.depends_db_session
) -> list[database.Catalog]:
    """List all outdated catalogs of a provider."""
    return (
        db_session.query(database.Catalog)
        .filter(database.Catalog.provider_id == provider_id)
        .filter(database.Catalog.valid_until < datetime.now(tz=UTC))
        .all()
    )


@router.post(
    "/{provider_id}/update",
    status_code=status.HTTP_200_OK,
    response_class=responses.JSONResponse,
)
async def post_provider_update(
    provider_id: int, db_session: Session = database.depends_db_session
) -> dict[str, str]:
    """Trigger an update of a providers catalogs."""
    if not db_session.get(database.Provider, provider_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    celery_task = fetch_provider.apply_async(
        args=[provider_id], retry_policy={"max_retries": 3}
    )
    return {"detail": "Update for provider scheduled", "task_uuid": celery_task.id}
