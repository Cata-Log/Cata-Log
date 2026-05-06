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

from cata_log.settings import Settings

COMMON_FILEHANDLER_CONFIG = {
    "level": "DEBUG",
    "class": "logging.handlers.RotatingFileHandler",
    "maxBytes": Settings.LOG_FILE_MAXSIZE.value,
    "backupCount": Settings.LOG_FILE_BACKUP_COUNT.value,
    "formatter": "json",
}

COMMON_LOGGER_CONFIG = {
    "level": "NOTSET",
    "propagate": True,
}

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "{asctime} ({levelname}) - {name}: {message}",
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
            "filename": str(Settings.LOGS_PATH.value / "root.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "uvicorn-logfile": {
            "filename": str(Settings.LOGS_PATH.value / "uvicorn.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "access-logfile": {
            "filename": str(Settings.LOGS_PATH.value / "access.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "cata-log-logfile": {
            "filename": str(Settings.LOGS_PATH.value / "cata-log.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "apscheduler-logfile": {
            "filename": str(Settings.LOGS_PATH.value / "apscheduler.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "alembic-logfile": {
            "filename": str(Settings.LOGS_PATH.value / "alembic.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "sqlalchemy-logfile": {
            "filename": str(Settings.LOGS_PATH.value / "sqlalchemy.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
    },
    "root": {
        "handlers": ["console", "root-logfile"],
        "level": Settings.LOG_LEVEL.value,
    },
    "loggers": {
        "uvicorn": {"handlers": ["uvicorn-logfile"], "level": "INFO"},
        "uvicorn.access": {
            "handlers": ["access-logfile"],
            "level": "INFO",
            "propagate": False,
        },
        "alembic": {"handlers": ["alembic-logfile"], **COMMON_LOGGER_CONFIG},
        "sqlalchemy": {"handlers": ["sqlalchemy-logfile"], **COMMON_LOGGER_CONFIG},
        "apscheduler": {"handlers": ["apscheduler-logfile"], **COMMON_LOGGER_CONFIG},
        "cata_log": {"handlers": ["cata-log-logfile"], **COMMON_LOGGER_CONFIG},
        "httpx": {"handlers": ["cata-log-logfile"], **COMMON_LOGGER_CONFIG},
    },
}
