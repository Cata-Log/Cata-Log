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

from apscheduler.events import EVENT_JOB_ERROR, JobExecutionEvent
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.job import Job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from cata_log import database
from cata_log.exceptions import NetworkError
from cata_log.settings import Settings

JOB_DATABASE_URL = "sqlite:////mnt/db/jobs.sqlite"

__all__ = ["JOB_DATABASE_URL", "fetch_provider", "scheduler"]

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=JOB_DATABASE_URL)},
    executors={"default": ThreadPoolExecutor(max_workers=1)},
    timezone=UTC,
    job_defaults={
        "replace_existing": True,
        "coalesce": True,
        "misfire_grace_time": 3600,
        "jobstore": "default",
        "executor": "default",
    },
)


def retry_on_network_error_listener(event: JobExecutionEvent) -> None:
    """Listener for job errors that schedules a retry job on networkerror.

    Args: event: The jobevent.
    """
    logger.critical("listener event match")
    if event.exception and isinstance(event.exception, NetworkError):
        logger.critical("listener triggered")
        job: Job | None = scheduler.get_job(event.job_id)
        if job:
            logger.critical("Job %s ran into networkerror", job.id)
            scheduler.add_job(
                job.func,
                args=job.args,
                id=job.id + "-retry",
                trigger=DateTrigger(event.scheduled_run_time + timedelta(seconds=10)),
                replace_existing=True,
            )


scheduler.add_listener(retry_on_network_error_listener, EVENT_JOB_ERROR)


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
        expiration_days = Settings.EXPIRATION_DAYS.value
        expiration_date = datetime.now(tz=UTC) - timedelta(days=expiration_days)
        database.Catalog.cleanup(db_session, expiration_date)


@scheduler.scheduled_job(
    id="cleanup-storage", trigger=CronTrigger(hour=0, minute=0, day_of_week=1)
)
def cleanup_storage() -> None:
    """Job to cleanup unused files from storage."""
    with database.DBSession() as db_session:
        database.PageFile.cleanup(db_session)
