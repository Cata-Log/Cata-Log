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
from datetime import UTC, timedelta

from apscheduler.events import EVENT_JOB_ERROR, JobExecutionEvent
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.job import Job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from cata_log.exceptions import NetworkError
from cata_log.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

JOB_DATABASE_URL = (
    get_settings().external_database_url
    or f"sqlite+pysqlite:///{settings.database_path / 'jobs.sqlite3'}"
)

scheduler = BackgroundScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=JOB_DATABASE_URL)},
    executors={"default": ThreadPoolExecutor(max_workers=1)},
    timezone=UTC,
    job_defaults={
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
    if event.exception and isinstance(event.exception, NetworkError):
        logger.debug("Retry listener triggered by network error.")
        job: Job | None = scheduler.get_job(event.job_id)
        if job:
            scheduler.add_job(
                job.func,
                args=job.args,
                id=job.id + "-retry",
                trigger=DateTrigger(
                    event.scheduled_run_time + timedelta(seconds=settings.retry_delay)
                ),
                replace_existing=True,
            )
            logger.info(
                "Job retry scheduled",
                extra={"job_id": job.id, "job_retry_time": job.next_run_time},
            )


scheduler.add_listener(retry_on_network_error_listener, EVENT_JOB_ERROR)
