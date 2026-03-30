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

from celery_sqlalchemy_v2_scheduler.models import (
    PeriodicTask,
)
from sqlalchemy import (
    Connection,
    delete,
    event,
    orm,
)

from cata_log.exceptions import (
    ProviderUnknownClassWarning,
)

from . import models
from .utils import get_or_create_crontab_schedule

logger = logging.getLogger(__name__)


@event.listens_for(models.Page, "before_delete")
def before_page_delete(
    mapper: orm.Mapper,  # noqa: ARG001  # required for event decorator
    connection: Connection,  # noqa: ARG001  # required for event decorator
    target: models.Page,
) -> None:
    """Event cleaning up a page file before deleting the page."""
    target.storage_path.unlink(missing_ok=True)
    logger.debug(
        "Success cleaning up page file of a deleted page.",
        extra={"page_id": target.id, "page_storage_path": target.storage_path},
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
            extra={"provider_id": target.id, "provider_class_id": target.class_id},
        )
        return
    with orm.Session(bind=connection) as db_session:
        crontab = get_or_create_crontab_schedule(
            db_session, provider_class.schedule, provider_class.region.timezone
        )
        task = PeriodicTask(
            name=f"{target.class_id}-{target.config}",
            task="cata_log.tasks.fetch_provider",
            args=f"[{target.id}]",
            crontab_id=crontab.id,
            enabled=True,
        )
        db_session.add(task)
        db_session.flush()
        db_session.execute(
            models.Provider.__table__.update()
            .where(models.Provider.id == target.id)
            .values(task_id=task.id)
        )
    logger.debug(
        "Success adding periodictask to a newly inserted provider.",
        extra={"provider_id": target.id, "task_id": target.task_id},
    )


@event.listens_for(models.Provider, "before_delete")
def before_provider_delete(
    mapper: orm.Mapper,  # noqa: ARG001  # required for event decorator
    connection: Connection,
    target: models.Provider,
) -> None:
    """Event cleaning up a providers task before deleting the provider."""
    connection.execute(delete(PeriodicTask).where(PeriodicTask.id == target.task_id))
    logger.debug(
        "Success cleaning up periodictask of a deleted provider.",
        extra={"provider_id": target.id, "task_id": target.task_id},
    )
