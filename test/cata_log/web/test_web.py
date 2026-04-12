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


def test_get_providers_webpage__noauth(full_database, noauth_client):
    response = noauth_client.get("/")

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_providers_webpage__bad_auth(full_database, bad_auth_client):
    response = bad_auth_client.get("/")

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_providers_webpage(full_database, client):
    response = client.get("/")

    assert response.status_code == 200


def test_get_provider_catalog_webpage__noauth(
    full_database, fake_provider, noauth_client
):
    response = noauth_client.get(f"/catalogs/provider/{fake_provider.id}/latest/")

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_provider_catalog_webpage__bad_auth(
    full_database, fake_provider, bad_auth_client
):
    response = bad_auth_client.get(f"/catalogs/provider/{fake_provider.id}/latest/")

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_provider_catalog_webpage(full_database, fake_provider, client):
    response = client.get(f"/catalogs/provider/{fake_provider.id}/latest/")

    assert response.status_code == 200


def test_get_provider_catalog_webpage__not_found(full_database, client):
    response = client.get("/catalogs/provider/324/latest/")

    assert response.status_code == 404


def test_get_catalog_webpage__noauth(full_database, fake_catalog, noauth_client):
    response = noauth_client.get(f"/catalogs/{fake_catalog.id}/")

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_catalog_webpage__bad_auth(full_database, fake_catalog, bad_auth_client):
    response = bad_auth_client.get(f"/catalogs/{fake_catalog.id}/")

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_catalog_webpage(full_database, fake_catalog, client):
    response = client.get(f"/catalogs/{fake_catalog.id}/")

    assert response.status_code == 200


def test_get_catalog_webpage__not_found(full_database, client):
    response = client.get("/catalogs/324/")

    assert response.status_code == 404
