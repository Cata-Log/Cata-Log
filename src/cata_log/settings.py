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

import functools
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any

from platformdirs import user_data_path, user_log_path
from pydantic import Field, IPvAnyAddress, NonNegativeInt, PositiveInt, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the Cata-Log server. You can configure the settings with these command-line arguments or environment variables starting with *CATA_LOG_*."""

    model_config = SettingsConfigDict(
        env_prefix="CATA_LOG_",
        cli_kebab_case=True,
        cli_parse_args=True,
        cli_ignore_unknown_args=True,  # otherwise sphinx build fails
    )

    username: str = Field(default="admin", description="Username for authentication")
    password: str = Field(
        default="",
        description="Password, keep this empty to allow no authentication at all.",
    )
    data_path: Path = Field(
        default=user_data_path("cata-log", appauthor=False, ensure_exists=False),
        description="Path to the directory for Cata-Log's data. Use the following path options for detailed control.",
    )
    storage_path: Path = Field(
        default=data_path.default / "storage",
        description="Path to the storage for catalog page files.",
    )
    database_path: Path = Field(
        default=data_path.default / "db",
        description="Path to the directory for the database files.",
    )
    plugin_path: Path = Field(
        default=data_path.default / "plugins",
        description="Path to the plugin directory.",
    )
    logs_path: Path = Field(
        default=user_log_path("cata-log", appauthor=False, ensure_exists=False),
        description="Path to the logfiles.",
    )
    external_database_url: str = Field(
        default="",
        description="URL of an external database. Only set this is you want to use an external database.",
    )
    dev_mode: bool = Field(
        default=False, description="Whether to run in development mode."
    )
    public_get: bool = Field(
        default=False,
        description="Set this to allow access to all GET endpoints without authentication.",
    )
    request_timeout: PositiveInt = Field(
        default=10, description="Timeout for requests to provider servers."
    )
    retry_delay: PositiveInt = Field(
        default=1800,
        description="Number of seconds to wait before retrying a failed job.",
    )
    expiration_days: NonNegativeInt = Field(
        default=14,
        description="Number of days after creation until old catalogs are deleted.",
    )
    log_level: str = Field(default="WARNING", description="Global loglevel")
    log_file_backup_count: NonNegativeInt = Field(
        default=5, description="Number of backup logfiles to keep."
    )
    log_file_maxsize: NonNegativeInt = Field(
        default=2097152, description="Maximum size of a single logfile."
    )  # 2 MB
    host: IPvAnyAddress = Field(
        default=IPv4Address("127.0.0.1"),
        description="The host address that Cata-Log should be served under.",
    )
    port: int = Field(
        default=2424, ge=1, le=64435, description="Portnumber for the server"
    )
    forwarded_allow_ips: str = Field(
        default="localhost,127.0.0.1",
        description="Comma separated list of IP Addresses to trust with proxy headers",
    )
    workers: PositiveInt = Field(
        default=1, description="Number of webworker processes to run."
    )

    @field_validator("*", mode="after")
    @classmethod
    def ensure_dirs(cls, value: Any) -> Any:  # noqa: ANN401 # no reason to be precise here
        """Create non-existent paths.

        Returns:
            The path.
        """
        if isinstance(value, Path):
            value.mkdir(exist_ok=True, parents=True)
        return value


@functools.lru_cache
def get_settings() -> Settings:
    """Get the current settings."""
    return Settings()
