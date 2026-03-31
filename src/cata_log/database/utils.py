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

from datetime import tzinfo

from celery.schedules import crontab
from celery_sqlalchemy_v2_scheduler.models import (
    CrontabSchedule,
)
from sqlalchemy import (
    orm,
)


def get_or_create_crontab_schedule(
    db_session: orm.Session, crontab: crontab, tz: tzinfo | None = None
) -> CrontabSchedule:
    """Get or create a crontabschedule from a crontab with a custom timezone.

    Note:
        Analogous to :func:`celery_sqlalchemy_v2_scheduler.models.CrontabSchedule.from_schedule`.

    Args:
        db_session: The database session to use.
        crontab: The crontab to make a model from.
        tz: The timezone of the crontab.

    Returns:
        The crontabschedule instance to the given data.
    """
    spec = {
        "minute": crontab._orig_minute,  # noqa: SLF001 ; the only way to do this
        "hour": crontab._orig_hour,  # noqa: SLF001
        "day_of_week": crontab._orig_day_of_week,  # noqa: SLF001
        "day_of_month": crontab._orig_day_of_month,  # noqa: SLF001
        "month_of_year": crontab._orig_month_of_year,  # noqa: SLF001
    }
    if tz is not None:
        spec.update({"timezone": getattr(tz, "zone", str(tz))})
    crontab_schedule = db_session.query(CrontabSchedule).filter_by(**spec).first()
    if not crontab_schedule:
        crontab_schedule = CrontabSchedule(**spec)
        db_session.add(crontab_schedule)
        db_session.commit()
    return crontab_schedule
