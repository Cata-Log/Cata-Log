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

import calendar
import enum
from pathlib import Path

STORAGE_PATH = Path("/mnt/storage/").resolve()
DATABASE_URL = "sqlite:////mnt/db/cata-log.sqlite3"
BROKER_URL = "amqp://guest:guest@localhost:5672//"
LOG_DIRECTORY_PATH = Path("/var/log/cata-log/").resolve()

FAST_API_TITLE = "Cata-Log"
FAST_API_DESCRIPTION = "The Central Hub For Grocery Store Catalogs"
FAST_API_SUMMARY = "API overview for Cata-Log"
FAST_API_LICENSE_INFO = {
    "name": "AGPL version 3 or later",
    "url": "https://www.gnu.org/licenses/agpl-3.0",
}
FAST_API_CONTACT = {
    "name": "Github Repo",
    "url": "https://github.com/Dacid99/cata-log.git",
}


class DefaultConfig(enum.StrEnum):
    """Enum listing all configuration defaults."""

    expiration_days = "28"
    fake_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    log_level = "INFO"
    log_file_backup_count = "10"
    log_file_maxsize = "2097152"  # 2 MB


class CatalogSchedules(enum.Enum):
    """Enum of all catalog schedule types."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class WeekCountingStartpoints(enum.Enum):
    """Enum of all common startpoints for counting a week from."""

    SUNDAY = calendar.Day.SUNDAY
    MONDAY = calendar.Day.MONDAY

    @property
    def week_number_format(self) -> str:
        """The datetime formatter for the enum value.

        Returns:
            The datetime formatter string.
        """
        return "%U" if self == calendar.Day.SUNDAY else "%W"
