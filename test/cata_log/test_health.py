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

import os
import shutil
from unittest.mock import patch

import psutil
import pytest
from sqlalchemy.sql import text

from cata_log.settings import get_settings


@pytest.fixture(autouse=True)
def healthy_shutil_diskusage():
    with patch(
        "shutil.disk_usage",
        return_value=shutil._ntuple_diskusage(total=1000, used=200, free=800),
    ) as patched_shutil_diskusage:
        yield patched_shutil_diskusage


@pytest.fixture(autouse=True)
def healthy_psutil_virtual_memory():
    with patch(
        "psutil.virtual_memory",
        return_value=psutil._ntp.svmem(
            total=1200,
            available=800,
            used=400,
            free=500,
            percent=33.3,
            active=600,
            inactive=500,
            buffers=100,
            cached=750,
            shared=150,
            slab=900,
        ),
    ) as patched_psutil_virtual_memory:
        yield patched_psutil_virtual_memory


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200


def test_health__noauth(noauth_client):
    response = noauth_client.get("/health")

    assert response.status_code == 200


def test_health__bad_auth(bad_auth_client):
    response = bad_auth_client.get("/health")

    assert response.status_code == 200


def test_health__scheduler_not_running(client, started_scheduler):
    started_scheduler.shutdown()

    response = client.get("/health")

    assert response.status_code == 500

    started_scheduler.start()


def test_health__full_diskspace(client, healthy_shutil_diskusage):
    healthy_shutil_diskusage.return_value = shutil._ntuple_diskusage(
        total=1000, used=950, free=50
    )

    response = client.get("/health")

    assert response.status_code == 500
    healthy_shutil_diskusage.assert_called_once()


def test_health__full_memory(client, healthy_psutil_virtual_memory):
    healthy_psutil_virtual_memory.return_value = psutil._ntp.svmem(
        total=1200,
        available=100,
        used=1100,
        free=50,
        percent=91.7,
        active=400,
        inactive=600,
        buffers=100,
        cached=900,
        shared=600,
        slab=900,
    )

    response = client.get("/health")

    assert response.status_code == 500
    healthy_psutil_virtual_memory.assert_called_once()


@patch("socket.create_connection", side_effect=OSError)
def test_health__no_internet(patched_socket_connection, client):
    response = client.get("/health")

    assert response.status_code == 500
    patched_socket_connection.assert_called_once()
