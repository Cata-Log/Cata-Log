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

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from celery import Celery
from celery.schedules import crontab

from cata_log import constants, database
from cata_log.constants import BROKER_URL, DATABASE_URL
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

logger = logging.getLogger(__name__)


@app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs: Any) -> None:  # noqa: ARG001  # extra kwargs required by celery decorator
    """Set up and register the default catalog cleanup task."""
    sender.add_periodic_task(schedule=crontab(hour=1), sig=cleanup_catalogs.s())


@app.task
def fetch_provider(provider_id: int) -> None:
    """Task for fetching all pages of a catalog from a provider.

    Args:
        provider_id: The database id of the provider to fetch.
    """
    logger.info("Fetching provider catalog ...", extra={"provider_id": provider_id})
    db_session = next(database.get_db_session())
    provider = db_session.get(database.Provider, provider_id)
    if provider:
        with provider.get_provider_instance() as provider_fetcher:
            new_catalog = database.Catalog(
                provider_id=provider_id,
                valid_since=provider_fetcher.get_valid_since().astimezone(UTC),
                valid_until=provider_fetcher.get_valid_until().astimezone(UTC),
            )
            db_session.add(new_catalog)
            db_session.flush()
            for page_number, page_bytes in provider_fetcher.iter_catalog_pages():
                page_storage_path = provider_fetcher.get_new_storage_path()
                logger.debug(
                    "Saving page data to storage ...",
                    extra={
                        "provider_id": provider_id,
                        "page_nr": page_number,
                        "storage_path": page_storage_path,
                    },
                )
                page_storage_path.write_bytes(page_bytes)
                logger.debug(
                    "Success saving page data to storage.",
                    extra={
                        "provider_id": provider_id,
                        "page_nr": page_number,
                        "storage_path": page_storage_path,
                    },
                )
                new_page = database.Page(
                    catalog_id=new_catalog.id,
                    number=page_number,
                    storage_path=str(page_storage_path),
                )
                db_session.add(new_page)
                db_session.flush()
        db_session.commit()
        return
    logger.error(
        "Failed to find provider from database!", extra={"provider_id": provider_id}
    )
    return


@app.task
def cleanup_catalogs() -> None:
    """Task to cleanup outdated catalogs."""
    db_session = next(database.get_db_session())
    expiration_days_string = get_config("expiration_days")
    try:
        expiration_days = int(expiration_days_string)
    except ValueError:
        expiration_days = int(constants.DefaultConfig.expiration_days)
    expiration_date = datetime.now(tz=UTC) - timedelta(days=expiration_days)
    logger.info(
        "Deleting outdated catalogs ...", extra={"expiration_deadline": expiration_date}
    )
    for catalog in (
        db_session.query(database.Catalog)
        .filter(database.Catalog.created_at < expiration_date)
        .all()
    ):
        logger.debug(
            "Deleting outdated catalog ...",
            extra={
                "catalog_id": catalog.id,
                "creation_date": catalog.created_at,
                "expiration_deadline": expiration_date,
            },
        )
        db_session.delete(catalog)
        db_session.flush()
        logger.debug(
            "Success deleting outdated catalog.",
            extra={
                "catalog_id": catalog.id,
                "creation_date": catalog.created_at,
                "expiration_deadline": expiration_date,
            },
        )
    db_session.commit()
    logger.info(
        "Success deleting outdated catalogs.",
        extra={"expiration_deadline": expiration_date},
    )
