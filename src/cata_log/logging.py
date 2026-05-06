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

from cata_log.constants import LOG_DIRECTORY_PATH
from cata_log.settings import Settings

COMMON_FILEHANDLER_CONFIG = {
    "level": "DEBUG",
    "class": "logging.handlers.RotatingFileHandler",
    "maxBytes": Settings.LOG_FILE_MAXSIZE.value,
    "backupCount": Settings.LOG_FILE_BACKUP_COUNT.value,
    "formatter": "json",
}

COMMON_LOGGER_CONFIG = {
    "level": Settings.LOG_LEVEL.value,
    "propagate": True,
}

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "{asctime} ({levelname}) - {name}: {module}.{funcName}:{lineno} - {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "format": "{asctime}{levelname}{name}{module}{funcName}{lineno}{message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "root-logfile": {
            "filename": str(LOG_DIRECTORY_PATH / "root.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "cata-log-logfile": {
            "filename": str(LOG_DIRECTORY_PATH / "cata-log.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "amqp-logfile": {
            "filename": str(LOG_DIRECTORY_PATH / "amqp.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "apscheduler-logfile": {
            "filename": str(LOG_DIRECTORY_PATH / "apscheduler.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "sqlalchemy-logfile": {
            "filename": str(LOG_DIRECTORY_PATH / "sqlalchemy.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "fastapi-logfile": {
            "filename": str(LOG_DIRECTORY_PATH / "fastapi.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
    },
    "root": {
        "handlers": ["root-logfile"],
        "level": Settings.LOG_LEVEL.value,
    },
    "loggers": {
        "uvicorn": {"handlers": ["console", "fastapi-logfile"], **COMMON_LOGGER_CONFIG},
        "starlette": {
            "handlers": ["console", "fastapi-logfile"],
            **COMMON_LOGGER_CONFIG,
        },
        "sqlalchemy": {"handlers": ["sqlalchemy-logfile"], **COMMON_LOGGER_CONFIG},
        "amqp": {"handlers": ["amqp-logfile"], **COMMON_LOGGER_CONFIG},
        "apscheduler": {"handlers": ["apscheduler-logfile"], **COMMON_LOGGER_CONFIG},
        "cata_log": {
            "handlers": ["console", "cata-log-logfile"],
            **COMMON_LOGGER_CONFIG,
        },
    },
}


def setup_logging() -> None:
    """Set up logging."""
    logging.config.dictConfig(LOGGING_CONFIG)
