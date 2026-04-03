import enum
import os
from typing import override


class Config(enum.StrEnum):
    """Enum listing all configuration defaults."""

    REQUEST_TIMEOUT = "10"
    EXPIRATION_DAYS = "14"
    LOG_LEVEL = "INFO"
    LOG_FILE_BACKUP_COUNT = "10"
    LOG_FILE_MAXSIZE = "2097152"  # 2 MB

    @property
    @override
    def value(self) -> str:
        return os.environ.get(self.name, None) or super().value
