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

import logging.config
from importlib import resources

import alembic.command
import uvicorn
from alembic.config import Config

from cata_log.app import create_fastapi_app

if __name__ == "__main__":
    import cata_log.logging
    import cata_log.scheduler
    from cata_log.settings import get_settings

    settings = get_settings()

    logging.config.dictConfig(cata_log.logging.CATA_LOG_LOGGING_CONFIG)

    with resources.path("cata_log.migrations", "alembic.ini") as path:
        alembic_config = Config(path)
    alembic.command.upgrade(config=alembic_config, revision="head")

    cata_log.scheduler.scheduler.start()

    uvicorn.run(
        app=create_fastapi_app(),
        host=str(settings.host),
        port=settings.port,
        forwarded_allow_ips=settings.forwarded_allow_ips,
        log_config=cata_log.logging.UVICORN_LOGGING_CONFIG,
        log_level=settings.log_level,
        reload=settings.dev_mode,
        workers=settings.workers,
    )
