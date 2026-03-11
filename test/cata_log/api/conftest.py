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

import pytest
from fastapi.testclient import TestClient

from cata_log.database import get_db_session


@pytest.fixture
def patched_fastapi_app(fake_fs, mock_get_db_session):
    # fastapi app needs to be imported after fs is patched
    from cata_log.main import app  # noqa: PLC0415

    app.dependency_overrides[get_db_session] = mock_get_db_session
    return app


@pytest.fixture
def client(patched_fastapi_app):
    return TestClient(patched_fastapi_app)
