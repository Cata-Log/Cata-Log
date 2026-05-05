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


import contextlib
import logging

from apscheduler.jobstores.sqlalchemy import JobLookupError
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import Connection, Engine, delete, event, orm
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.pool.base import _ConnectionRecord

from cata_log.exceptions import (
    ProviderUnknownClassWarning,
)
from cata_log.jobs import scheduler

from . import models

logger = logging.getLogger(__name__)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(
    dbapi_connection: DBAPIConnection,
    connection_record: _ConnectionRecord,  # noqa: ARG001  # required for event decorator
) -> None:
    """Event setting pragmas on all engines after connecting to db."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


@event.listens_for(models.PageFile, "after_delete")
def after_pagefile_delete(
    mapper: orm.Mapper,  # noqa: ARG001  # required for event decorator
    connection: Connection,  # noqa: ARG001  # required for event decorator
    target: models.PageFile,
) -> None:
    """Event cleaning up a page file after deleting the file from db."""
    target.path.unlink(missing_ok=True)
    logger.debug(
        "Success cleaning up page file of a deleted page.",
        extra={"pagefile_id": target.id, "pagefile_path": target.path},
    )


@event.listens_for(models.Page, "after_delete")
def after_page_delete(
    mapper: orm.Mapper,  # noqa: ARG001  # required for event decorator
    connection: Connection,
    target: models.Page,
) -> None:
    """Event cleaning up an orphaned page file after deleting the page."""
    if len(target.file.pages) == 1:
        connection.execute(
            delete(models.PageFile).where(models.PageFile.id == target.file_id)
        )


@event.listens_for(models.Provider, "after_insert")
def after_provider_insert(
    mapper: orm.Mapper,  # noqa: ARG001  # required for event decorator
    connection: Connection,
    target: models.Provider,
) -> None:
    """Event setting up a providers task after its insertion."""
    try:
        provider_class = target.get_provider_class()
    except ProviderUnknownClassWarning:
        logger.exception(
            "No provider class found for newly inserted provider instance!",
            extra={"provider_id": target.id, "provider_class_uid": target.class_uid},
        )
        return
    cron_trigger = CronTrigger.from_crontab(
        provider_class.schedule, timezone=provider_class.region.timezone
    )
    cron_trigger.jitter = provider_class.jitter
    job = scheduler.add_job(
        name=f"{target.class_uid}-{target.configuration}",
        func="cata_log.jobs:fetch_provider",
        args=[target.id],
        trigger=cron_trigger,
    )
    connection.execute(
        models.Provider.__table__.update()
        .where(models.Provider.id == target.id)
        .values(job_id=job.id)
    )
    logger.debug(
        "Success adding task to a newly inserted provider.",
        extra={"provider_id": target.id, "job_id": target.job_id},
    )


@event.listens_for(models.Provider, "after_delete")
def after_provider_delete(
    mapper: orm.Mapper,  # noqa: ARG001  # required for event decorator
    connection: Connection,  # noqa: ARG001  # required for event decorator
    target: models.Provider,
) -> None:
    """Event cleaning up a providers task after deleting the provider."""
    with contextlib.suppress(JobLookupError):
        scheduler.remove_job(target.job_id)
    logger.debug(
        "Success cleaning up periodictask of a deleted provider.",
        extra={"provider_id": target.id, "job_id": target.job_id},
    )


__all__ = [
    "after_page_delete",
    "after_pagefile_delete",
    "after_provider_delete",
    "after_provider_insert",
    "set_sqlite_pragma",
]
