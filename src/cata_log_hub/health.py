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

import logging
import shutil
import socket

import psutil
import sqlalchemy.exc
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from sqlalchemy.sql import text

from cata_log_hub.database import DBSession
from cata_log_hub.exceptions import HealthCheckFailedError
from cata_log_hub.scheduler import scheduler
from cata_log_hub.settings import get_settings

logger = logging.getLogger(__name__)

CRITICAL_RESOURCE_USAGE = 0.9


def check_scheduler() -> None:
    """Check whether the scheduler is up.

    Raises;
        HealthCheckFailedError: If the scheduler is down.
    """
    if not scheduler.running:
        logger.critical("Task scheduler is not running!")
        raise HealthCheckFailedError("Task scheduler is not running!")


def check_memory() -> None:
    """Check the memory usage.

    Raises;
        HealthCheckFailedError: If memory usage is high.
    """
    memory = psutil.virtual_memory()
    if memory.percent / 100 > CRITICAL_RESOURCE_USAGE:
        logger.critical(
            "Memory is becoming sparse! Used: %s, Total: %s", memory.used, memory.total
        )
        raise HealthCheckFailedError("Memory is becoming sparse!")


def check_diskspace() -> None:
    """Check the disk usage.

    Raises;
        HealthCheckFailedError: If disk usage is high.
    """
    disk_usage = shutil.disk_usage("/")
    if disk_usage.used / disk_usage.total > CRITICAL_RESOURCE_USAGE:
        logger.critical(
            "Disk space is becoming sparse! Used: %s, Total: %s",
            disk_usage.total,
            disk_usage.used,
        )
        raise HealthCheckFailedError("Disk space is becoming sparse!")


def check_database() -> None:
    """Check connection to the database.

    Raises;
        HealthCheckFailedError: If connecting to the database fails.
    """
    try:
        with DBSession() as db_session:
            if "sqlite" in db_session.get_bind().dialect.driver:  # pragma: no branch
                integrity_check_result = db_session.execute(
                    text("PRAGMA integrity_check;")
                ).fetchall()
                if integrity_check_result[0][0] != "ok":
                    logger.critical(
                        "Database integrity check failed! Errors: %s",
                        integrity_check_result,
                    )
                    raise HealthCheckFailedError("Database integrity check failed!")
                foreign_key_check_result = db_session.execute(
                    text("PRAGMA foreign_key_check;")
                ).fetchall()
                if foreign_key_check_result:
                    logger.critical(
                        "Database foreign key integrity check failed! Errors: %s",
                        foreign_key_check_result,
                    )
                    raise HealthCheckFailedError(
                        "Database foreign key integrity check failed!"
                    )
            db_session.execute(text("SELECT 1"))
    except sqlalchemy.exc.SQLAlchemyError as database_error:
        logger.critical("Database is down!", exc_info=True)
        raise HealthCheckFailedError("Database is down!") from database_error


def check_internet() -> None:
    """Check the internet connection.

    Raises;
        HealthCheckFailedError: If no internet connection can be established.
    """
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=5)
    except OSError as error:
        logger.critical("No internet connection!", exc_info=True)
        raise HealthCheckFailedError("No internet connection!") from error


def check_storage_io() -> None:
    """Check writing the storage.

    Raises;
        HealthCheckFailedError: If an error occurs in IO with the storage.
    """
    settings = get_settings()
    try:
        (settings.storage_path / "testfile").write_text("test")
        (settings.storage_path / "testfile").unlink()
    except OSError as error:
        logger.critical("Can't write storage files!", exc_info=True)
        raise HealthCheckFailedError("Can't write storage files!") from error


def check() -> None:
    """Check the health of the different parts of the application.

    Raises;
        HealthCheckFailedError: If any healthcheck fails.
    """
    check_database()
    check_scheduler()
    check_storage_io()
    check_diskspace()
    check_memory()
    check_internet()
    logger.info("Healthcheck passed successfully.")


router = APIRouter(prefix="", include_in_schema=False)


@router.get("/health", status_code=200)
def healthcheck() -> None:
    """HTTP endpoint to trigger healthchecks."""
    try:
        check()
    except HealthCheckFailedError as error:
        raise HTTPException(detail=str(error), status_code=500) from error
