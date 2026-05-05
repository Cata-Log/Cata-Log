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
from sqlalchemy.sql import text

from cata_log.constants import STORAGE_PATH
from cata_log.database import DBSession
from cata_log.exceptions import HealthCheckFailedError
from cata_log.jobs import scheduler

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
    if memory.used / memory.total > CRITICAL_RESOURCE_USAGE:
        logger.critical(
            "Memory is becoming sparse! Used: %s, Total: %s", memory.used, memory.total
        )
        raise HealthCheckFailedError("Memory is becoming sparse!")


def check_diskspace() -> None:
    """Check the disk usage.

    Raises;
        HealthCheckFailedError: If disk usage is high.
    """
    total, used, _ = shutil.disk_usage("/")
    if used / total > CRITICAL_RESOURCE_USAGE:
        logger.critical(
            "Disk space is becoming sparse! Used: %s, Total: %s", total, used
        )
        raise HealthCheckFailedError("Disk space is becoming sparse!")


def check_database() -> None:
    """Check connection to the database.

    Raises;
        HealthCheckFailedError: If connecting to the database fails.
    """
    try:
        with DBSession() as db_session:
            db_session.execute(text("SELECT 1 FROM providers"))
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
    try:
        (STORAGE_PATH / "testfile").write_text("test")
        (STORAGE_PATH / "testfile").unlink()
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
