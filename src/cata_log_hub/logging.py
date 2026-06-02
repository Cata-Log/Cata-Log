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

from cata_log_hub.settings import get_settings

settings = get_settings()

COMMON_FILEHANDLER_CONFIG = {
    "level": "DEBUG",
    "class": "logging.handlers.RotatingFileHandler",
    "maxBytes": settings.log_file_maxsize,
    "backupCount": settings.log_file_backup_count,
    "formatter": "json",
}

COMMON_LOGGER_CONFIG = {
    "level": "NOTSET",
    "propagate": True,
}

CATA_LOG_LOGGING_CONFIG = {
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
            "filename": str(settings.logs_path / "root.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "cata-log-logfile": {
            "filename": str(settings.logs_path / "cata-log-hub.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "apscheduler-logfile": {
            "filename": str(settings.logs_path / "apscheduler.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "alembic-logfile": {
            "filename": str(settings.logs_path / "alembic.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "sqlalchemy-logfile": {
            "filename": str(settings.logs_path / "sqlalchemy.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
    },
    "root": {
        "handlers": ["console", "root-logfile"],
        "level": settings.log_level,
    },
    "loggers": {
        "alembic": {"handlers": ["alembic-logfile"], **COMMON_LOGGER_CONFIG},
        "sqlalchemy": {"handlers": ["sqlalchemy-logfile"], **COMMON_LOGGER_CONFIG},
        "apscheduler": {"handlers": ["apscheduler-logfile"], **COMMON_LOGGER_CONFIG},
        "cata_log_hub": {"handlers": ["cata-log-logfile"], **COMMON_LOGGER_CONFIG},
        "httpx": {"handlers": ["cata-log-logfile"], **COMMON_LOGGER_CONFIG},
    },
}

UVICORN_LOGGING_CONFIG = {
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
            "filename": str(settings.logs_path / "root.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "uvicorn-logfile": {
            "filename": str(settings.logs_path / "uvicorn.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "access-logfile": {
            "filename": str(settings.logs_path / "access.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
    },
    "root": {
        "handlers": ["console", "root-logfile"],
        "level": settings.log_level,
    },
    "loggers": {
        "uvicorn": {"handlers": ["uvicorn-logfile"], "level": "INFO"},
        "uvicorn.error": {"handlers": ["uvicorn-logfile"], "level": "INFO"},
        "uvicorn.access": {
            "handlers": ["access-logfile"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
