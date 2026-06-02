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

from datetime import datetime

import pytest

from cata_log_hub.constants import WeekCountingStartpoints
from cata_log_hub.utils import dates


@pytest.mark.parametrize(
    ("datetime", "week_counting_startpoint", "expected_week_number"),
    [
        (datetime(2025, 1, 1), WeekCountingStartpoints.MONDAY, 1),
        (datetime(2025, 1, 1), WeekCountingStartpoints.SUNDAY, 1),
        (datetime(2026, 3, 24), WeekCountingStartpoints.MONDAY, 13),
        (datetime(2026, 3, 24), WeekCountingStartpoints.SUNDAY, 13),
        (datetime(2026, 5, 25), WeekCountingStartpoints.SUNDAY, 22),
        (datetime(2026, 5, 25), WeekCountingStartpoints.MONDAY, 22),
    ],
)
def test_get_calendar_week_number(
    datetime, week_counting_startpoint, expected_week_number
):
    result = dates.get_calendar_week_number(datetime, week_counting_startpoint)

    assert result == expected_week_number
