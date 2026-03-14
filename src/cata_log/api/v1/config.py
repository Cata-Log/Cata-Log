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
from cata_log.constants import DefaultConfig

router = APIRouter(prefix="/config", tags=["config"])


class Config(BaseModel):
    """Config data model."""

    name: str
    value: str


class ConfigUpdate(BaseModel):
    """Config update data model."""

    value: str


class NewConfig(BaseModel):
    """Config creation data model."""

    name: str
    value: str


@router.get("", response_model=list[Config])
async def list_config(
    db_session: orm.Session = database.depends_db_session,
) -> list[database.Config]:
    """List all configurations."""
    return db_session.query(database.Config).all()


@router.get("/defaults", response_model=list[Config])
async def list_config_defaults() -> list[DefaultConfig]:
    """List all configuration defaults."""
    return list(DefaultConfig)


@router.get("/{key}", response_model=Config)
async def get_config(
    key: str, db_session: orm.Session = database.depends_db_session
) -> database.Config:
    """Get a single configuration."""
    config = (
        db_session.query(database.Config).filter(database.Config.name == key).first()
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Config not found"
        )
    return config


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Config)
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


@router.put("/{key}", response_model=Config)
async def put_config(
    key: str,
    config_update: ConfigUpdate,
    db_session: orm.Session = database.depends_db_session,
) -> database.Config:
    """Update a single configuration."""
    config = (
        db_session.query(database.Config).filter(database.Config.name == key).first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    config.value = config_update.value
    db_session.commit()
    db_session.refresh(config)
    return config


@router.patch("/{key}", response_model=Config)
async def patch_config(
    key: str,
    config_update: ConfigUpdate,
    db_session: orm.Session = database.depends_db_session,
) -> database.Config:
    """Update a single configuration."""
    config = (
        db_session.query(database.Config).filter(database.Config.name == key).first()
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Config not found"
        )
    config.value = config_update.value
    db_session.commit()
    db_session.refresh(config)
    return config


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    key: str, db_session: orm.Session = database.depends_db_session
) -> None:
    """Delete a single configuration."""
    config = (
        db_session.query(database.Config)
        .filter(database.Config.name == key)
        .one_or_none()
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Config not found"
        )
    db_session.delete(config)
    db_session.commit()
