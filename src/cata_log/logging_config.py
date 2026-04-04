import logging.config

from cata_log.config import Settings
from cata_log.constants import LOG_DIRECTORY_PATH

COMMON_FILEHANDLER_CONFIG = {
    "level": "DEBUG",
    "class": "logging.handlers.RotatingFileHandler",
    "maxBytes": int(Settings.LOG_FILE_MAXSIZE),
    "backupCount": int(Settings.LOG_FILE_BACKUP_COUNT),
    "formatter": "json",
}

COMMON_LOGGER_CONFIG = {
    "level": Settings.LOG_LEVEL,
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
        "celery-logfile": {
            "filename": str(LOG_DIRECTORY_PATH / "celery.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "sqlalchemy-logfile": {
            "filename": str(LOG_DIRECTORY_PATH / "sqlalchemy.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
        "uvicorn-logfile": {
            "filename": str(LOG_DIRECTORY_PATH / "uvicorn.log"),
            **COMMON_FILEHANDLER_CONFIG,
        },
    },
    "root": {
        "handlers": ["root-logfile"],
        "level": Settings.LOG_LEVEL,
    },
    "loggers": {
        "uvicorn": {"handlers": ["console", "uvicorn-logfile"], **COMMON_LOGGER_CONFIG},
        "celery": {"handlers": ["celery-logfile"], **COMMON_LOGGER_CONFIG},
        "sqlalchemy": {"handlers": ["sqlalchemy-logfile"], **COMMON_LOGGER_CONFIG},
        "amqp": {"handlers": ["amqp-logfile"], **COMMON_LOGGER_CONFIG},
        "cata_log": {
            "handlers": ["console", "cata-log-logfile"],
            **COMMON_LOGGER_CONFIG,
        },
    },
}


def setup_logging() -> None:
    """Set up logging."""
    logging.config.dictConfig(LOGGING_CONFIG)
