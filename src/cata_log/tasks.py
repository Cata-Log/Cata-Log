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

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from celery import Celery
from celery.schedules import crontab

from cata_log import constants, database
from cata_log.constants import BROKER_URL, DATABASE_URL
from cata_log.providers import Provider
from cata_log.utils.shortcuts import get_config

app = Celery()

app.conf.update(
    beat_scheduler="celery_sqlalchemy_v2_scheduler.schedulers.DatabaseScheduler",
    beat_dburi=DATABASE_URL,
    broker_url=BROKER_URL,
    result_backend="db+" + DATABASE_URL,
    result_engine_options={"echo": True},
    enable_utc=True,
)


@app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs: Any) -> None:
    sender.add_periodic_task(schedule=crontab(hour=1), sig=cleanup_catalogs.s())


@app.task
def fetch_provider(provider_id: int) -> None:
    db_session = next(database.get_db_session())
    provider = (
        db_session.query(database.Provider)
        .filter(database.Provider.id == provider_id)
        .one_or_none()
    )
    if provider:
        catalog_class = Provider.registry.get(provider.class_id)
        if catalog_class:
            try:
                provider_fetcher = catalog_class(**provider.config)
            except TypeError:
                return
            new_catalog = database.Catalog(
                provider_id=provider_id,
                valid_since=provider_fetcher.get_valid_since().astimezone(UTC),
                valid_until=provider_fetcher.get_valid_until().astimezone(UTC),
            )
            db_session.add(new_catalog)
            db_session.flush()
            for page_number, page_bytes in provider_fetcher.iter_catalog_pages():
                page_storage_path = constants.STORAGE_PATH / str(uuid.uuid4())
                page_storage_path.write_bytes(page_bytes)
                new_page = database.Page(
                    catalog_id=new_catalog.id,
                    number=page_number,
                    storage_path=str(page_storage_path),
                )
                db_session.add(new_page)
                db_session.flush()
            db_session.commit()


@app.task
def cleanup_catalogs() -> None:
    db_session = next(database.get_db_session())
    expiration_days_string = get_config("expiration_days")
    try:
        expiration_days = int(expiration_days_string)
    except ValueError:
        expiration_days = int(constants.DefaultConfig.expiration_days)
    expiration_date = datetime.now(tz=UTC) - timedelta(days=expiration_days)
    for catalog in (
        db_session.query(database.Catalog)
        .filter(database.Catalog.created_at < expiration_date)
        .all()
    ):
        db_session.delete(catalog)
        db_session.flush()
    db_session.commit()
