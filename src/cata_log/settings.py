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

import enum
import os
from typing import Any, override

from cata_log.exceptions import ApplicationMisconfiguredError


class Settings(enum.Enum):
    """Enum listing all configuration defaults."""

    PUBLIC_GET = False
    REQUEST_TIMEOUT = 10
    RETRY_DELAY = 1800
    EXPIRATION_DAYS = 14
    LOG_LEVEL = "INFO"
    LOG_FILE_BACKUP_COUNT = 5
    LOG_FILE_MAXSIZE = 2097152  # 2 MB

    @property
    @override
    def value(self) -> Any:
        default = super().value
        return type(default)(os.environ.get(self.name, default))

    @classmethod
    def check(cls) -> None:
        """Checks the validity of all settings."""
        bad_configs = []
        for setting in cls:
            try:
                _ = setting.value
            except TypeError, ValueError:
                bad_configs.append(setting.name)
        if bad_configs:
            raise ApplicationMisconfiguredError(bad_configs)
