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

from argparse import ArgumentParser
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, Self

from platformdirs import user_data_path, user_log_path
from pydantic import Field, IPvAnyAddress, NonNegativeInt, PositiveInt, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Enum listing all configuration defaults."""

    data_path: Path = Field(
        default=user_data_path("cata-log", appauthor=False, ensure_exists=False),
        description="Path to the ",
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
    debug: bool = Field(default=False, description="Whether to run in debug mode.")
    port: int = Field(
        default=2424, ge=1, le=64435, description="Portnumber for the server"
    )
    host: IPvAnyAddress = Field(
        default=IPv4Address("127.0.0.1"),
        description="The host address that Cata-Log should be served under.",
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
    log_level: str = Field(default="INFO", description="Global loglevel")
    log_file_backup_count: NonNegativeInt = Field(
        default=5, description="Number of backup logfiles to keep."
    )
    log_file_maxsize: NonNegativeInt = Field(
        default=2097152, description="Maximum size of a single logfile."
    )  # 2 MB
    forwarded_allow_ips: str = Field(
        default="localhost,127.0.0.1",
        description="Comma separated list of IP Addresses to trust with proxy headers",
    )
    username: str = Field(default="admin", description="Username for authentication")
    password: str = Field(
        default="",
        description="Password, keep this empty to allow no authentication at all.",
    )
    workers: PositiveInt = Field(
        default=1, description="Number of webworker processes to run."
    )

    class Config:
        """Config metadata for pydantic model."""

        env_prefix = "CATA_LOG_"

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

    @classmethod
    def load(cls) -> Self:
        """Load settings from args or env.

        Returns:
            The settings instance.
        """
        parser = ArgumentParser(
            prog="Cata-Log",
            description="Start the Cata-Log server. You can configure the settings with the command-line arguments or with environment variables starting with CATA_LOG_.",
        )
        for name, field in cls.model_fields.items():
            arg_name = "--" + name.replace("_", "-")

            parser.add_argument(
                arg_name,
                type=field.annotation or str,
                default=None,
                help=f"default: {field.default}; {field.description}",
            )
        args = parser.parse_args()
        return cls(
            **{key: value for key, value in vars(args).items() if value is not None}
        )


settings = Settings.load()
