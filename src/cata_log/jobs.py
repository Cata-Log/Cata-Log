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

from apscheduler.triggers.cron import CronTrigger

from cata_log import database
from cata_log.scheduler import scheduler
from cata_log.settings import settings

logger = logging.getLogger(__name__)


def fetch_provider(provider_id: int) -> None:
    """Job for fetching all pages of a catalog from a provider.

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


@scheduler.scheduled_job(id="cleanup-catalogs", trigger=CronTrigger(hour=1, minute=0))
def cleanup_catalogs() -> None:
    """Job to cleanup outdated catalogs."""
    with database.DBSession() as db_session:
        expiration_days = settings.expiration_days
        if expiration_days:
            expiration_date = datetime.now(tz=UTC) - timedelta(days=expiration_days)
            database.Catalog.cleanup(db_session, expiration_date)


@scheduler.scheduled_job(
    id="cleanup-storage", trigger=CronTrigger(hour=0, minute=0, day_of_week=1)
)
def cleanup_storage() -> None:
    """Job to cleanup unused files from storage."""
    with database.DBSession() as db_session:
        database.PageFile.cleanup(db_session)
