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

from cata_log import database


def test_list_providers(client):
    response = client.get("/api/v1/providers")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_list_available_providers(client):
    response = client.get("/api/v1/providers/available")

    assert response.status_code == 200
    assert response.json()


def test_list_provider_current_catalogs(fake_catalog_current, client):
    response = client.get(
        f"/api/v1/providers/{fake_catalog_current.provider_id}/catalogs/current"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]
    assert data[0]["id"] == fake_catalog_current.id


def test_list_provider_previews_catalogs(fake_catalog_preview, client):
    response = client.get(
        f"/api/v1/providers/{fake_catalog_preview.provider_id}/catalogs/previews"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]
    assert data[0]["id"] == fake_catalog_preview.id


def test_list_provider_outdated_catalogs(fake_catalog_outdated, client):
    response = client.get(
        f"/api/v1/providers/{fake_catalog_outdated.provider_id}/catalogs/outdated"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]
    assert data[0]["id"] == fake_catalog_outdated.id


def test_get_provider(fake_provider, client):
    response = client.get(f"/api/v1/providers/{fake_provider.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_provider.id


def test_get_provider__not_found(client):
    response = client.get("/api/v1/providers/456")

    assert response.status_code == 404
    assert response.json() == {"detail": "Provider not found"}


def test_delete_provider(LocalSession, fake_provider, client):
    response = client.delete(f"/api/v1/providers/{fake_provider.id}")

    assert response.status_code == 204
    assert not LocalSession().query(database.Provider).all()


def test_delete_provider__not_found(client):
    response = client.delete("/api/v1/providers/230")

    assert response.status_code == 404
    assert response.json() == {"detail": "Provider not found"}


def test_post_provider__success(LocalSession, client):
    response = client.post(
        url="/api/v1/providers",
        json={"class_id": "rewe", "config": {"markt_id": "1234"}},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["class_id"] == "rewe"
    assert data["config"] == {"markt_id": "1234"}
    assert (
        LocalSession()
        .query(database.Provider)
        .filter(database.Provider.id == data["id"])
        .one_or_none()
    )


def test_post_provider__missing_config(LocalSession, client):
    response = client.post(
        url="/api/v1/providers",
        json={"class_id": "rewe", "config": {}},
    )

    assert response.status_code == 400
    assert not LocalSession().query(database.Provider).all()


def test_post_provider__bad_class_id(LocalSession, client):
    response = client.post(
        url="/api/v1/providers",
        json={"class_id": "lu9%z", "config": {}},
    )

    assert response.status_code == 400
    assert not LocalSession().query(database.Provider).all()


def test_update_provider__not_found(client):
    response = client.post(
        url="/api/v1/providers/987/update",
    )

    assert response.status_code == 404
