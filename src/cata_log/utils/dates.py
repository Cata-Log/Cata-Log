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

import datetime

from cata_log import constants


def get_calendar_week_number(
    dt: datetime.datetime,
    week_startpoint: constants.WeekCountingStartpoints = constants.WeekCountingStartpoints.MONDAY,
):
    week_number_offset = (
        1
        if (
            int(
                datetime.date(dt.year, 1, 1).strftime(
                    week_startpoint.week_number_format
                )
            )
            == 0
        )
        else 0
    )
    return int(dt.strftime(week_startpoint.week_number_format)) + week_number_offset


def get_week_limit_dates(
    dt: datetime.datetime,
    week_startpoint: constants.WeekCountingStartpoints = constants.WeekCountingStartpoints.MONDAY,
) -> tuple[datetime.datetime, datetime.datetime]:
    start = (
        dt - datetime.timedelta(days=dt.weekday()) + week_startpoint.week_start_weekday
    )
    end = (
        dt
        + datetime.timedelta(days=6 - dt.weekday())
        + week_startpoint.week_start_weekday
    )
    return start, end
