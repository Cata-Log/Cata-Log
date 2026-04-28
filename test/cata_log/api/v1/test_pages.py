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


from urllib.parse import urljoin

import pytest

from cata_log import security
from cata_log.api.v1 import common


def test_list_pages(full_database, fake_page, client):
    response = client.get("/api/v1/pages")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]
    assert data[0]["id"] == fake_page.id
    assert data[0]["catalog_id"] == fake_page.catalog_id
    assert data[0]["number"] == fake_page.number


def test_list_pages__noauth(full_database, noauth_client):
    response = noauth_client.get("/api/v1/pages")

    assert response.status_code == 401
    security.HTTP401Error.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_list_pages__bad_auth(full_database, bad_auth_client):
    response = bad_auth_client.get("/api/v1/pages")

    assert response.status_code == 401
    security.HTTP401Error.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_list_pages__noauth__public_get(
    full_database, fake_page, noauth_client, public_get
):
    response = noauth_client.get("/api/v1/pages")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]
    assert data[0]["id"] == fake_page.id
    assert data[0]["catalog_id"] == fake_page.catalog_id
    assert data[0]["number"] == fake_page.number


def test_get_page(fake_page, client):
    response = client.get(f"/api/v1/pages/{fake_page.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_page.id


def test_get_page__noauth(fake_page, noauth_client):
    response = noauth_client.get(f"/api/v1/pages/{fake_page.id}")

    assert response.status_code == 401
    security.HTTP401Error.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_page__bad_auth(fake_page, bad_auth_client):
    response = bad_auth_client.get(f"/api/v1/pages/{fake_page.id}")

    assert response.status_code == 401
    security.HTTP401Error.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_page__noauth__public_get(fake_page, noauth_client, public_get):
    response = noauth_client.get(f"/api/v1/pages/{fake_page.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_page.id


def test_get_page__not_found(client):
    response = client.get("/api/v1/pages/456")

    assert response.status_code == 404
    common.HTTPStatusError.model_validate(response.json())
    assert response.json() == {"detail": "Page not found"}


@pytest.mark.parametrize(("filename"), [None, "page_image.png"])
def test_download_page(fake_page, fake_file, client, filename):
    response = client.get(
        urljoin(
            f"/api/v1/pages/{fake_page.id}/download",
            f"?filename={filename}" if filename else "",
        )
    )

    assert response.status_code == 200
    assert response.content == fake_file.read_bytes()
    assert "content-disposition" in response.headers
    assert (
        response.headers["content-disposition"]
        == f'attachment; filename="{filename or fake_file.name}"'
    )


def test_download_page__noauth(fake_page, noauth_client):
    response = noauth_client.get(f"/api/v1/pages/{fake_page.id}/download")

    assert response.status_code == 401
    security.HTTP401Error.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_download_page__bad_auth(fake_page, bad_auth_client):
    response = bad_auth_client.get(f"/api/v1/pages/{fake_page.id}/download")

    assert response.status_code == 401
    security.HTTP401Error.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_download_page__noauth__public_get(
    fake_page, fake_file, noauth_client, public_get
):
    response = noauth_client.get(
        f"/api/v1/pages/{fake_page.id}/download",
    )

    assert response.status_code == 200
    assert response.content == fake_file.read_bytes()
    assert "content-disposition" in response.headers
    assert (
        response.headers["content-disposition"]
        == f'attachment; filename="{fake_file.name}"'
    )


def test_download_page__not_found(client):
    response = client.get("/api/v1/pages/456/download")

    assert response.status_code == 404
    common.HTTPStatusError.model_validate(response.json())
    assert response.json() == {"detail": "Page not found"}


@pytest.mark.parametrize(("filename"), [None, "page_image.png"])
def test_embed_page(fake_page, fake_file, client, filename):
    response = client.get(
        urljoin(
            f"/api/v1/pages/{fake_page.id}/embed",
            f"?filename={filename}" if filename else "",
        )
    )

    assert response.status_code == 200
    assert response.content == fake_file.read_bytes()
    assert "content-disposition" in response.headers
    assert (
        response.headers["content-disposition"]
        == f'inline; filename="{filename or fake_file.name}"'
    )


def test_embed_page__noauth(fake_page, noauth_client):
    response = noauth_client.get(f"/api/v1/pages/{fake_page.id}/embed")

    assert response.status_code == 401
    security.HTTP401Error.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_embed_page__bad_auth(fake_page, bad_auth_client):
    response = bad_auth_client.get(f"/api/v1/pages/{fake_page.id}/embed")

    assert response.status_code == 401
    security.HTTP401Error.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_embed_page(fake_page, fake_file, noauth_client, public_get):
    response = noauth_client.get(
        f"/api/v1/pages/{fake_page.id}/embed",
    )

    assert response.status_code == 200
    assert response.content == fake_file.read_bytes()
    assert "content-disposition" in response.headers
    assert (
        response.headers["content-disposition"]
        == f'inline; filename="{fake_file.name}"'
    )


def test_embed_page__not_found(client):
    response = client.get("/api/v1/pages/456/embed")

    assert response.status_code == 404
    common.HTTPStatusError.model_validate(response.json())
    assert response.json() == {"detail": "Page not found"}
