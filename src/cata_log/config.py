import enum
import os
from typing import override


class Config(enum.StrEnum):
    """Enum listing all configuration defaults."""

    request_timeout = "10"
    expiration_days = "28"
    log_level = "INFO"
    log_file_backup_count = "10"
    log_file_maxsize = "2097152"  # 2 MB

    @property
    @override
    def value(self) -> str:
        return os.environ.get(self.name, None) or super().value
