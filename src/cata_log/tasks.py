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
from cata_log.exceptions import NetworkError
from cata_log.utils.shortcuts import get_config

app = Celery()

app.conf.update(
    beat_scheduler="celery_sqlalchemy_v2_scheduler.schedulers.DatabaseScheduler",
    beat_dburi=DATABASE_URL,
    broker_url=BROKER_URL,
    result_backend=None,
    task_annotations={"*": {"autoretry_for": (NetworkError,), "max_retries": 3}},
    task_ignore_result=True,
    task_acks_late=False,
)

logger = logging.getLogger(__name__)


@app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs: Any) -> None:  # noqa: ARG001  # extra kwargs required by celery decorator
    """Set up and register the default catalog cleanup task."""
    sender.add_periodic_task(
        schedule=crontab(hour=1, minute=0), sig=cleanup_catalogs.s()
    )


@app.task
def fetch_provider(provider_id: int) -> None:
    """Task for fetching all pages of a catalog from a provider.

    Args:
        provider_id: The database id of the provider to fetch.
    """
    logger.info("Fetching provider catalog ...", extra={"provider_id": provider_id})
    with database.DBSession() as db_session:
        provider = db_session.get(database.Provider, provider_id)
        if provider:
            provider.fetch_catalog(db_session)
        else:
            logger.error(
                "Failed to find provider from database!",
                extra={"provider_id": provider_id},
            )


@app.task
def cleanup_catalogs() -> None:
    """Task to cleanup outdated catalogs."""
    with database.DBSession() as db_session:
        expiration_days_string = get_config("expiration_days")
        try:
            expiration_days = int(expiration_days_string)
        except ValueError:
            expiration_days = int(constants.DefaultConfig.expiration_days)
        expiration_date = datetime.now(tz=UTC) - timedelta(days=expiration_days)
        database.Catalog.cleanup(db_session, expiration_date)
