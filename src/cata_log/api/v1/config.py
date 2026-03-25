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
from pydantic import BaseModel
from sqlalchemy import orm

from cata_log import database
from cata_log.api.mixins import TimestampMixin
from cata_log.constants import DefaultConfig

router = APIRouter(prefix="/config", tags=["config"])


class ConfigDefault(BaseModel):
    """Config default data model."""

    name: str
    value: str


class Config(ConfigDefault, TimestampMixin):
    """Config data model."""


class ConfigUpdate(BaseModel):
    """Config update data model."""

    value: str


class NewConfig(BaseModel):
    """Config creation data model."""

    name: str
    value: str


@router.get("", response_model=list[Config], operation_id="list-configs-v1")
async def list_config(
    db_session: orm.Session = database.depends_db_session,
) -> list[database.Config]:
    """List all configurations."""
    return db_session.query(database.Config).all()


@router.get(
    "/defaults",
    response_model=list[ConfigDefault],
    operation_id="list-default-configs-v1",
)
async def list_config_defaults() -> list[DefaultConfig]:
    """List all configuration defaults."""
    return list(DefaultConfig)


@router.get("/{name}", response_model=Config, operation_id="get-config-v1")
async def get_config(
    name: str, db_session: orm.Session = database.depends_db_session
) -> database.Config:
    """Get a single configuration."""
    try:
        config = db_session.query(database.Config).filter(
            database.Config.name == name
        ).one_or_none() or database.Config(
            name=name, value=getattr(DefaultConfig, name)
        )
    except AttributeError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Config not found"
        ) from None
    return config


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Config,
    operation_id="set-config-v1",
)
async def post_config(
    new_config: NewConfig, db_session: orm.Session = database.depends_db_session
) -> database.Config:
    """Set a new configuration."""
    if (
        db_session.query(database.Config)
        .filter(database.Config.name == new_config.name)
        .one_or_none()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Config already exists"
        )
    config = database.Config(**new_config.model_dump())
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)
    return config


@router.patch("/{name}", response_model=Config, operation_id="update-config-v1")
async def patch_config(
    name: str,
    config_update: ConfigUpdate,
    db_session: orm.Session = database.depends_db_session,
) -> database.Config:
    """Update a single configuration."""
    config = (
        db_session.query(database.Config)
        .filter(database.Config.name == name)
        .one_or_none()
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Config not found"
        )
    config.value = config_update.value
    db_session.commit()
    db_session.refresh(config)
    return config


@router.delete(
    "/{name}", status_code=status.HTTP_204_NO_CONTENT, operation_id="delete-config-v1"
)
async def delete_config(
    name: str, db_session: orm.Session = database.depends_db_session
) -> None:
    """Delete a single configuration."""
    config = (
        db_session.query(database.Config)
        .filter(database.Config.name == name)
        .one_or_none()
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Config not found"
        )
    db_session.delete(config)
    db_session.commit()
