import logging.config

from constants import LOG_DIRECTORY_PATH, DefaultConfig
from utils.shortcuts import get_config

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "format": "{asctime}{levelname}{name}{module}{funcName}{lineno}{message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "logfile": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(LOG_DIRECTORY_PATH / "cata-log.log"),
                "maxBytes": int(
                    get_config(DefaultConfig.log_file_maxsize.name),
                ),
                "backupCount": int(
                    get_config(DefaultConfig.log_file_backup_count.name)
                ),
                "formatter": "default",
            },
        },
        "root": {
            "handlers": ["console", "logfile"],
            "level": getattr(
                logging,
                get_config(DefaultConfig.log_level.name),
                "INFO",
            ),
        },
    },
)
