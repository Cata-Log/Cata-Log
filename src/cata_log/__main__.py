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

from importlib import resources

import alembic.command
import uvicorn
from alembic.config import Config

if __name__ == "__main__":
    from cata_log import logging, scheduler
    from cata_log.settings import settings

    with resources.path("cata_log.migrations", "alembic.ini") as path:
        alembic_config = Config(path)
    alembic.command.upgrade(config=alembic_config, revision="head")

    scheduler.scheduler.start()

    uvicorn.run(
        app="cata_log.app:app",
        host=str(settings.host),
        port=settings.port,
        forwarded_allow_ips=settings.forwarded_allow_ips,
        log_config=logging.LOGGING_CONFIG,
        log_level=settings.log_level,
        reload=settings.debug,
        workers=settings.workers,
    )
