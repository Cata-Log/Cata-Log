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


def test_webui_startpage__noauth(full_database, noauth_client):
    response = noauth_client.get("/")

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_webui_startpage__bad_auth(full_database, bad_auth_client):
    response = bad_auth_client.get("/")

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_webui_startpage(full_database, client):
    response = client.get("/")

    assert response.status_code == 200


def test_webui_catalog__noauth(full_database, fake_provider, noauth_client):
    response = noauth_client.get(f"/catalogs/provider/{fake_provider.id}/latest/")

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_webui_catalog__bad_auth(full_database, fake_provider, bad_auth_client):
    response = bad_auth_client.get(f"/catalogs/provider/{fake_provider.id}/latest/")

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_webui_catalog(full_database, fake_provider, client):
    response = client.get(f"/catalogs/provider/{fake_provider.id}/latest/")

    assert response.status_code == 200
