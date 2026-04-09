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

from copy import copy, deepcopy
from unittest.mock import MagicMock, patch
from urllib.parse import urljoin

import pytest
from celery.app.task import Task

from cata_log import database


@pytest.fixture
def mock_fetch_provider_task(monkeypatch):
    mock_task = MagicMock(spec=Task)
    monkeypatch.setattr("cata_log.api.v1.providers.fetch_provider", mock_task)
    return mock_task


def test_list_providers(full_database, client):
    response = client.get("/api/v1/providers")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_list_providers__noauth(full_database, noauth_client):
    response = noauth_client.get("/api/v1/providers")

    assert response.status_code == 401


def test_list_providers__bad_auth(full_database, bad_auth_client):
    response = bad_auth_client.get("/api/v1/providers")

    assert response.status_code == 401


def test_list_providers__noauth__public_get(full_database, noauth_client, public_get):
    response = noauth_client.get("/api/v1/providers")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.parametrize(
    ("querystring"),
    [("?region=deutschland"), ("?region=us"), (""), ("?query=test"), ("?query=aldi")],
)
def test_list_available_providers(client, querystring):
    response = client.get(urljoin("/api/v1/providers/available", querystring or ""))

    assert response.status_code == 200


def test_list_available_providers__noauth(noauth_client):
    response = noauth_client.get("/api/v1/providers/available")

    assert response.status_code == 401


def test_list_available_providers__bad_auth(bad_auth_client):
    response = bad_auth_client.get("/api/v1/providers/available")

    assert response.status_code == 401


def test_list_available_providers__noauth__public_get(noauth_client, public_get):
    response = noauth_client.get("/api/v1/providers/available")

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


def test_list_provider_catalogs__noauth(full_database, fake_provider, noauth_client):
    response = noauth_client.get(f"/api/v1/providers/{fake_provider.id}/catalogs")

    assert response.status_code == 401


def test_list_provider_catalogs__bad_auth(
    full_database, fake_provider, bad_auth_client
):
    response = bad_auth_client.get(f"/api/v1/providers/{fake_provider.id}/catalogs")

    assert response.status_code == 401


def test_list_provider_catalogs__noauth__public_get(
    full_database, fake_provider, fake_catalog_preview, noauth_client, public_get
):
    response = noauth_client.get(f"/api/v1/providers/{fake_provider.id}/catalogs")

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


def test_list_provider_current_catalog__noauth(
    full_database, fake_catalog_current, noauth_client
):
    response = noauth_client.get(
        f"/api/v1/providers/{fake_catalog_current.provider_id}/catalogs/current"
    )

    assert response.status_code == 401


def test_list_provider_current_catalog__bad_auth(
    full_database, fake_catalog_current, bad_auth_client
):
    response = bad_auth_client.get(
        f"/api/v1/providers/{fake_catalog_current.provider_id}/catalogs/current"
    )

    assert response.status_code == 401


def test_list_provider_current_catalog__noauth__public_get(
    full_database, fake_catalog_current, noauth_client, public_get
):
    response = noauth_client.get(
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


def test_list_provider_previews_catalogs__noauth(
    full_database, fake_catalog_preview, noauth_client
):
    response = noauth_client.get(
        f"/api/v1/providers/{fake_catalog_preview.provider_id}/catalogs/previews"
    )

    assert response.status_code == 401


def test_list_provider_previews_catalogs__bad_auth(
    full_database, fake_catalog_preview, bad_auth_client
):
    response = bad_auth_client.get(
        f"/api/v1/providers/{fake_catalog_preview.provider_id}/catalogs/previews"
    )

    assert response.status_code == 401


def test_list_provider_previews_catalogs__noauth__public_get(
    full_database, fake_catalog_preview, noauth_client, public_get
):
    response = noauth_client.get(
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


def test_list_provider_outdated_catalogs__noauth(
    full_database, fake_catalog_outdated, noauth_client
):
    response = noauth_client.get(
        f"/api/v1/providers/{fake_catalog_outdated.provider_id}/catalogs/outdated"
    )

    assert response.status_code == 401


def test_list_provider_outdated_catalogs__bad_auth(
    full_database, fake_catalog_outdated, bad_auth_client
):
    response = bad_auth_client.get(
        f"/api/v1/providers/{fake_catalog_outdated.provider_id}/catalogs/outdated"
    )

    assert response.status_code == 401


def test_list_provider_outdated_catalogs__noauth__public_get(
    full_database, fake_catalog_outdated, noauth_client, public_get
):
    response = noauth_client.get(
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


def test_get_latest_provider_catalog__noauth(
    full_database, fake_provider, fake_latest_catalog, noauth_client
):
    response = noauth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest"
    )

    assert response.status_code == 401


def test_get_latest_provider_catalog__bad_auth(
    full_database, fake_provider, fake_latest_catalog, bad_auth_client
):
    response = bad_auth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest"
    )

    assert response.status_code == 401


def test_get_latest_provider_catalog__noauth__public_get(
    full_database, fake_provider, fake_latest_catalog, noauth_client, public_get
):
    response = noauth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest"
    )

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


def test_list_latest_provider_catalog_pages__noauth(
    full_database, fake_provider, fake_latest_catalog, noauth_client
):
    response = noauth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages"
    )

    assert response.status_code == 401


def test_list_latest_provider_catalog_pages__bad_auth(
    full_database, fake_provider, fake_latest_catalog, bad_auth_client
):
    response = bad_auth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages"
    )

    assert response.status_code == 401


def test_list_latest_provider_catalog_pages__noauth__public_get(
    full_database, fake_provider, fake_latest_catalog, noauth_client, public_get
):
    response = noauth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages"
    )

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


def test_get_latest_provider_catalog_page__noauth(
    full_database, fake_provider, fake_page, noauth_client
):
    response = noauth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}"
    )

    assert response.status_code == 401


def test_get_latest_provider_catalog_page__bad_auth(
    full_database, fake_provider, fake_page, bad_auth_client
):
    response = bad_auth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}"
    )

    assert response.status_code == 401


def test_get_latest_provider_catalog_page__noauth__public_get(
    full_database, fake_provider, fake_page, noauth_client, public_get
):
    response = noauth_client.get(
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
        urljoin(
            f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}/download",
            f"?filename={filename}" if filename else "",
        )
    )

    assert response.status_code == 200
    assert response.content == fake_page_file.read_bytes()
    assert "content-disposition" in response.headers
    assert (
        response.headers["content-disposition"]
        == f'attachment; filename="{filename or fake_page_file.name}"'
    )


def test_download_latest_provider_catalog_page__noauth(
    full_database, fake_provider, fake_page, noauth_client
):
    response = noauth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}/download"
    )

    assert response.status_code == 401


def test_download_latest_provider_catalog_page__bad_auth(
    full_database, fake_provider, fake_page, bad_auth_client
):
    response = bad_auth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}/download"
    )

    assert response.status_code == 401


def test_download_latest_provider_catalog_page__noauth__public_get(
    full_database, fake_provider, fake_page, fake_page_file, noauth_client, public_get
):
    response = noauth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}/download",
    )

    assert response.status_code == 200
    assert response.content == fake_page_file.read_bytes()
    assert "content-disposition" in response.headers
    assert (
        response.headers["content-disposition"]
        == f'attachment; filename="{fake_page_file.name}"'
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
        urljoin(
            f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}/embed",
            f"?filename={filename}" if filename else "",
        )
    )

    assert response.status_code == 200
    assert response.content == fake_page_file.read_bytes()
    assert "content-disposition" in response.headers
    assert (
        response.headers["content-disposition"]
        == f'inline; filename="{filename or fake_page_file.name}"'
    )


def test_embed_latest_provider_catalog_page__noauth(
    full_database, fake_provider, fake_page, noauth_client
):
    response = noauth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}/embed"
    )

    assert response.status_code == 401


def test_embed_latest_provider_catalog_page__bad_auth(
    full_database, fake_provider, fake_page, bad_auth_client
):
    response = bad_auth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}/embed"
    )

    assert response.status_code == 401


def test_embed_latest_provider_catalog_page__noauth__public_get(
    full_database, fake_provider, fake_page, fake_page_file, noauth_client, public_get
):
    response = noauth_client.get(
        f"/api/v1/providers/{fake_provider.id}/catalogs/latest/pages/{fake_page.number}/embed",
    )

    assert response.status_code == 200
    assert response.content == fake_page_file.read_bytes()
    assert "content-disposition" in response.headers
    assert (
        response.headers["content-disposition"]
        == f'inline; filename="{fake_page_file.name}"'
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


def test_get_provider__noauth(fake_provider, noauth_client):
    response = noauth_client.get(f"/api/v1/providers/{fake_provider.id}")

    assert response.status_code == 401


def test_get_provider__bad_auth(fake_provider, bad_auth_client):
    response = bad_auth_client.get(f"/api/v1/providers/{fake_provider.id}")

    assert response.status_code == 401


def test_get_provider__noauth__public_get(fake_provider, noauth_client, public_get):
    response = noauth_client.get(f"/api/v1/providers/{fake_provider.id}")

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


def test_delete_provider__noauth(LocalSession, fake_provider, noauth_client):
    response = noauth_client.delete(f"/api/v1/providers/{fake_provider.id}")

    assert response.status_code == 401


def test_delete_provider__bad_auth(LocalSession, fake_provider, bad_auth_client):
    response = bad_auth_client.delete(f"/api/v1/providers/{fake_provider.id}")

    assert response.status_code == 401


def test_delete_provider__noauth__public_get(
    LocalSession, fake_provider, noauth_client, public_get
):
    response = noauth_client.delete(f"/api/v1/providers/{fake_provider.id}")

    assert response.status_code == 401


def test_delete_provider__not_found(client):
    response = client.delete("/api/v1/providers/230")

    assert response.status_code == 404
    assert response.json() == {"detail": "Provider not found"}


def test_patch_provider(LocalSession, fake_provider, client, mock_fetch_provider_task):
    old_config = deepcopy(fake_provider.config)

    response = client.patch(
        url=f"/api/v1/providers/{fake_provider.id}",
        json={
            "config": {
                **old_config,
                "optional_config": "some value",
            }
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["class_id"] == fake_provider.class_id
    assert data["config"] == {**old_config, "optional_config": "some value"}
    with LocalSession() as db_session:
        provider = db_session.get(database.Provider, fake_provider.id)
    assert provider.class_id == data["class_id"]
    assert provider.config == data["config"]
    mock_fetch_provider_task.delay.assert_called_once_with(fake_provider.id)


def test_patch_provider__noauth(fake_provider, noauth_client, mock_fetch_provider_task):
    response = noauth_client.patch(
        url=f"/api/v1/providers/{fake_provider.id}",
        json={
            "config": {
                **fake_provider.config,
                "optional_config": "config abc",
            }
        },
    )

    assert response.status_code == 401
    mock_fetch_provider_task.delay.assert_not_called()


def test_patch_provider__bad_auth(
    fake_provider, bad_auth_client, mock_fetch_provider_task
):
    response = bad_auth_client.patch(
        url=f"/api/v1/providers/{fake_provider.id}",
        json={
            "config": {
                **fake_provider.config,
                "optional_config": "config abc",
            }
        },
    )

    assert response.status_code == 401
    mock_fetch_provider_task.delay.assert_not_called()


def test_patch_provider__noauth__public_get(
    fake_provider, noauth_client, public_get, mock_fetch_provider_task
):
    response = noauth_client.patch(
        url=f"/api/v1/providers/{fake_provider.id}",
        json={
            "config": {
                **fake_provider.config,
                "optional_config": "config abc",
            }
        },
    )

    assert response.status_code == 401
    mock_fetch_provider_task.delay.assert_not_called()


def test_patch_provider__not_found(client, mock_fetch_provider_task):
    response = client.patch(
        "/api/v1/providers/230",
        json={"config": {"markt_id": "marktqwertz"}},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Provider not found"}
    mock_fetch_provider_task.delay.assert_not_called()


def test_patch_provider__missing_config(
    fake_provider, client, mock_fetch_provider_task
):
    response = client.patch(
        url=f"/api/v1/providers/{fake_provider.id}",
        json={"config": {}},
    )

    assert response.status_code == 400
    mock_fetch_provider_task.delay.assert_not_called()


def test_patch_provider__extra_config(fake_provider, client, mock_fetch_provider_task):
    response = client.patch(
        url=f"/api/v1/providers/{fake_provider.id}",
        json={
            "config": {
                **fake_provider.config,
                "optional_config": "config abc",
                "extra": "random",
            }
        },
    )

    assert response.status_code == 200
    assert "extra" not in response.json()["config"]
    assert response.json()["config"]["optional_config"] == "config abc"
    mock_fetch_provider_task.delay.assert_called_once_with(fake_provider.id)


def test_patch_provider__duplicate(
    db_session, fake_provider, client, mock_fetch_provider_task
):
    other_provider = database.Provider(
        class_id=fake_provider.class_id,
        config={**fake_provider.config, "optional_config": "test opt"},
    )
    db_session.add(other_provider)
    db_session.flush()

    assert len(db_session.query(database.Provider).all()) == 2

    response = client.patch(
        url=f"/api/v1/providers/{fake_provider.id}",
        json={"config": other_provider.config},
    )

    assert response.status_code == 400
    assert fake_provider.config != other_provider.config
    mock_fetch_provider_task.delay.assert_not_called()


def test_patch_provider__no_change(
    LocalSession, fake_provider, client, mock_fetch_provider_task
):
    response = client.patch(
        url=f"/api/v1/providers/{fake_provider.id}",
        json={"config": fake_provider.config},
    )

    assert response.status_code == 200
    assert response.json()["config"] == fake_provider.config
    mock_fetch_provider_task.delay.assert_called_once_with(fake_provider.id)


def test_post_provider(
    LocalSession, client, provider_test_class, mock_fetch_provider_task
):
    response = client.post(
        url="/api/v1/providers",
        json={
            "class_id": provider_test_class.id(),
            "config": dict(provider_test_class.default_config),
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["class_id"] == provider_test_class.id()
    assert data["config"] == provider_test_class.validate_config(
        provider_test_class.default_config
    )
    with LocalSession() as db_session:
        new_provider = db_session.get(database.Provider, data["id"])
        assert new_provider
        assert new_provider.class_id == data["class_id"]
        assert new_provider.config == data["config"]
    mock_fetch_provider_task.delay.assert_called_once_with(data["id"])


def test_post_provider__noauth(
    noauth_client, provider_test_class, mock_fetch_provider_task
):
    response = noauth_client.post(
        url="/api/v1/providers",
        json={
            "class_id": provider_test_class.id(),
            "config": dict(provider_test_class.default_config),
        },
    )

    assert response.status_code == 401
    mock_fetch_provider_task.delay.assert_not_called()


def test_post_provider__bad_auth(
    bad_auth_client, provider_test_class, mock_fetch_provider_task
):
    response = bad_auth_client.post(
        url="/api/v1/providers",
        json={
            "class_id": provider_test_class.id(),
            "config": dict(provider_test_class.default_config),
        },
    )

    assert response.status_code == 401
    mock_fetch_provider_task.delay.assert_not_called()


def test_post_provider__missing_config(
    LocalSession, client, provider_test_class, mock_fetch_provider_task
):
    response = client.post(
        url="/api/v1/providers",
        json={
            "class_id": provider_test_class.id(),
            "config": {},
        },
    )

    assert response.status_code == 400
    with LocalSession() as db_session:
        assert not db_session.query(database.Provider).all()
    mock_fetch_provider_task.delay.assert_not_called()


def test_post_provider__noauth__public_get(
    noauth_client, public_get, provider_test_class, mock_fetch_provider_task
):
    response = noauth_client.post(
        url="/api/v1/providers",
        json={
            "class_id": provider_test_class.id(),
            "config": dict(provider_test_class.default_config),
        },
    )

    assert response.status_code == 401
    mock_fetch_provider_task.delay.assert_not_called()


def test_post_provider__extra_config(
    client, provider_test_class, mock_fetch_provider_task
):
    response = client.post(
        url="/api/v1/providers",
        json={
            "class_id": provider_test_class.id(),
            "config": {**provider_test_class.default_config, "extra": "extradata"},
        },
    )

    assert response.status_code == 201
    assert "extra" not in response.json()["config"]
    data = response.json()
    assert data["config"] == provider_test_class.validate_config(
        provider_test_class.default_config
    )
    mock_fetch_provider_task.delay.assert_called_once_with(data["id"])


def test_post_provider__bad_class_id(LocalSession, client, mock_fetch_provider_task):
    response = client.post(
        url="/api/v1/providers",
        json={"class_id": "lu9%z", "config": {}},
    )

    assert response.status_code == 400
    with LocalSession() as db_session:
        assert not db_session.query(database.Provider).all()
    mock_fetch_provider_task.delay.assert_not_called()


def test_post_provider__duplicate(
    LocalSession, fake_provider, client, mock_fetch_provider_task
):
    response = client.post(
        url="/api/v1/providers",
        json={"class_id": fake_provider.class_id, "config": fake_provider.config},
    )

    assert response.status_code == 400
    with LocalSession() as db_session:
        assert len(db_session.query(database.Provider).all()) == 1
    mock_fetch_provider_task.delay.assert_not_called()


def test_update_provider(fake_provider, client, mock_fetch_provider_task):
    response = client.post(
        url=f"/api/v1/providers/{fake_provider.id}/update",
    )

    assert response.status_code == 200
    mock_fetch_provider_task.delay.assert_called_once_with(fake_provider.id)


def test_update_provider__noauth(
    fake_provider, noauth_client, mock_fetch_provider_task
):
    response = noauth_client.post(
        url=f"/api/v1/providers/{fake_provider.id}/update",
    )

    assert response.status_code == 401
    mock_fetch_provider_task.delay.assert_not_called()


def test_update_provider__bad_auth(
    fake_provider, bad_auth_client, mock_fetch_provider_task
):
    response = bad_auth_client.post(
        url=f"/api/v1/providers/{fake_provider.id}/update",
    )

    assert response.status_code == 401
    mock_fetch_provider_task.delay.assert_not_called()


def test_update_provider__noauth__public_get(
    fake_provider, noauth_client, public_get, mock_fetch_provider_task
):
    response = noauth_client.post(
        url=f"/api/v1/providers/{fake_provider.id}/update",
    )

    assert response.status_code == 401
    mock_fetch_provider_task.delay.assert_not_called()


def test_update_provider__not_found(client, mock_fetch_provider_task):
    response = client.post(
        url="/api/v1/providers/987/update",
    )

    assert response.status_code == 404
    mock_fetch_provider_task.delay.assert_not_called()
