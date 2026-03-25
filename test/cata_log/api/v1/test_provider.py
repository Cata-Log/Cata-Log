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

from cata_log import database


def test_list_providers(full_database, client):
    response = client.get("/api/v1/providers")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.parametrize(
    ("querystring"),
    [("?region=deutschland"), ("?region=us"), (""), ("?query=test"), ("?query=aldi")],
)
def test_list_available_providers(client, querystring):
    response = client.get("/api/v1/providers/available" + querystring or "")

    assert response.status_code == 200


def test_list_provider_catalogs(
    full_database, fake_provider, fake_catalog_preview, client
):
    response = client.get(f"/api/v1/providers/{fake_provider.id}/catalogs")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]
    assert data[0]["id"] == fake_catalog_preview.id


def test_list_provider_current_catalog(full_database, fake_catalog_current, client):
    response = client.get(
        f"/api/v1/providers/{fake_catalog_current.provider_id}/catalogs/current"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]
    assert data[0]["id"] == fake_catalog_current.id


def test_list_provider_previews_catalogs(full_database, fake_catalog_preview, client):
    response = client.get(
        f"/api/v1/providers/{fake_catalog_preview.provider_id}/catalogs/previews"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]
    assert data[0]["id"] == fake_catalog_preview.id


def test_list_provider_outdated_catalogs(full_database, fake_catalog_outdated, client):
    response = client.get(
        f"/api/v1/providers/{fake_catalog_outdated.provider_id}/catalogs/outdated"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]
    assert data[0]["id"] == fake_catalog_outdated.id


def test_get_latest_provider_catalog(
    full_database, fake_provider, fake_latest_catalog, client
):
    response = client.get(f"/api/v1/providers/{fake_provider.id}/catalogs/latest")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_latest_catalog.id


def test_get_latest_provider_catalog__not_found(fake_provider, client):
    response = client.get(f"/api/v1/providers/{fake_provider.id}/catalogs/latest")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Catalog not found"


def test_list_latest_provider_catalog_pages(
    full_database, fake_provider, fake_latest_catalog, client
):
    response = client.get(f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]
    assert data[0]["id"] == fake_latest_catalog.pages[0].id


def test_get_latest_provider_catalog_pages__no_catalog(fake_provider, client):
    response = client.get(f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_get_latest_provider_catalog_page(
    full_database, fake_provider, fake_page, client
):
    response = client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_page.id


def test_get_latest_provider_catalog_page__catalog_not_found(fake_provider, client):
    response = client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/972"
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Page not found"


def test_get_latest_provider_catalog_page__page_not_found(
    full_database, fake_provider, client
):
    response = client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/972"
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Page not found"


@pytest.mark.parametrize(("filename"), [None, "page_image.png"])
def test_download_latest_provider_catalog_page(
    full_database, fake_provider, fake_page, fake_page_file, client, filename
):
    response = client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}/download"
        + (f"?filename={filename}" if filename else "")
    )

    assert response.status_code == 200
    assert response.content == fake_page_file.read_bytes()
    assert "content-disposition" in response.headers
    assert (
        response.headers["content-disposition"]
        == f'attachment; filename="{filename or fake_page_file.name}"'
    )


def test_download_latest_provider_catalog_page__catalog_not_found(
    fake_provider, client
):
    response = client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/972/download"
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Page not found"


def test_download_latest_provider_catalog_page__page_not_found(
    full_database, fake_provider, client
):
    response = client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/972/download"
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Page not found"


@pytest.mark.parametrize(("filename"), [None, "page_image.png"])
def test_embed_latest_provider_catalog_page(
    full_database, fake_provider, fake_page, fake_page_file, client, filename
):
    response = client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}/embed"
        + (f"?filename={filename}" if filename else "")
    )

    assert response.status_code == 200
    assert response.content == fake_page_file.read_bytes()
    assert "content-disposition" in response.headers
    assert (
        response.headers["content-disposition"]
        == f'inline; filename="{filename or fake_page_file.name}"'
    )


def test_embed_latest_provider_catalog_page__catalog_not_found(fake_provider, client):
    response = client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/972/embed"
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Page not found"


def test_embed_latest_provider_catalog_page__page_not_found(
    full_database, fake_provider, client
):
    response = client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/972/embed"
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Page not found"


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
    with LocalSession() as db_session:
        assert not db_session.query(database.Provider).all()


def test_delete_provider__not_found(client):
    response = client.delete("/api/v1/providers/230")

    assert response.status_code == 404
    assert response.json() == {"detail": "Provider not found"}


def test_patch_provider__success(LocalSession, fake_provider, client):
    response = client.patch(
        url=f"/api/v1/providers/{fake_provider.id}",
        json={"config": {"markt_id": "marktqwertz"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["class_id"] == "rewe-deutschland"
    assert data["config"] == {"markt_id": "marktqwertz"}
    with LocalSession() as db_session:
        provider = db_session.get(database.Provider, fake_provider.id)
    assert provider.config == data["config"]


def test_patch_provider__missing_config(fake_provider, client):
    response = client.patch(
        url=f"/api/v1/providers/{fake_provider.id}",
        json={"config": {}},
    )

    assert response.status_code == 400


def test_patch_provider__duplicate(LocalSession, fake_provider, client):
    provider = database.Provider(class_id=fake_provider.class_id, config={})
    with LocalSession() as db_session:
        db_session.add(provider)
        db_session.flush()

    response = client.patch(
        url=f"/api/v1/providers/{fake_provider.id}",
        json={"config": provider.config},
    )

    assert response.status_code == 400


def test_post_provider__success(LocalSession, client):
    response = client.post(
        url="/api/v1/providers",
        json={"class_id": "rewe-deutschland", "config": {"markt_id": "1234"}},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["class_id"] == "rewe-deutschland"
    assert data["config"] == {"markt_id": "1234"}
    with LocalSession() as db_session:
        assert db_session.get(database.Provider, data["id"])


def test_post_provider__missing_config(LocalSession, client):
    response = client.post(
        url="/api/v1/providers",
        json={"class_id": "rewe-deutschland", "config": {}},
    )

    assert response.status_code == 400
    with LocalSession() as db_session:
        assert not db_session.query(database.Provider).all()


def test_post_provider__bad_class_id(LocalSession, client):
    response = client.post(
        url="/api/v1/providers",
        json={"class_id": "lu9%z", "config": {}},
    )

    assert response.status_code == 400
    with LocalSession() as db_session:
        assert not db_session.query(database.Provider).all()


def test_post_provider__duplicate(LocalSession, fake_provider, client):
    response = client.post(
        url="/api/v1/providers",
        json={"class_id": fake_provider.class_id, "config": fake_provider.config},
    )

    assert response.status_code == 400
    with LocalSession() as db_session:
        assert len(db_session.query(database.Provider).all()) == 1


def test_update_provider__not_found(client):
    response = client.post(
        url="/api/v1/providers/987/update",
    )

    assert response.status_code == 404
