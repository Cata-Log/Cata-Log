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


from io import BytesIO
from urllib.parse import urljoin

import pytest
from pypdf import PdfReader

from cata_log_hub.api import common


def test_list_catalogs(full_database, client):
    response = client.get("/api/v1/catalogs")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 3


def test_list_catalogs__noauth(full_database, noauth_client):
    response = noauth_client.get("/api/v1/catalogs")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_list_catalogs__bad_auth(full_database, bad_auth_client):
    response = bad_auth_client.get("/api/v1/catalogs")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_list_catalogs__noauth__public_get(full_database, noauth_client, public_get):
    response = noauth_client.get("/api/v1/catalogs")

    assert response.status_code == 200


def test_list_latest_catalogs(full_database, fake_latest_catalog, client):
    response = client.get("/api/v1/catalogs/latest")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]
    assert data["results"][0]["id"] == fake_latest_catalog.id


def test_list_latest_catalogs__noauth(full_database, noauth_client):
    response = noauth_client.get("/api/v1/catalogs/latest")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_list_latest_catalogs__bad_auth(full_database, bad_auth_client):
    response = bad_auth_client.get("/api/v1/catalogs/latest")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_list_latest_catalogs__noauth__public_get(
    full_database, fake_latest_catalog, noauth_client, public_get
):
    response = noauth_client.get("/api/v1/catalogs/latest")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]
    assert data["results"][0]["id"] == fake_latest_catalog.id


def test_list_previews_catalogs(full_database, fake_catalog_preview, client):
    response = client.get("/api/v1/catalogs/previews")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]
    assert data["results"][0]["id"] == fake_catalog_preview.id


def test_list_previews_catalogs__noauth(full_database, noauth_client):
    response = noauth_client.get("/api/v1/catalogs/previews")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_list_previews_catalogs__bad_auth(full_database, bad_auth_client):
    response = bad_auth_client.get("/api/v1/catalogs/previews")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_list_previews_catalogs__noauth__public_get(
    full_database, fake_catalog_preview, noauth_client, public_get
):
    response = noauth_client.get("/api/v1/catalogs/previews")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]
    assert data["results"][0]["id"] == fake_catalog_preview.id


def test_list_current_catalogs(full_database, fake_catalog_current, client):
    response = client.get("/api/v1/catalogs/current")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]
    assert data["results"][0]["id"] == fake_catalog_current.id


def test_list_current_catalogs__noauth(full_database, noauth_client):
    response = noauth_client.get("/api/v1/catalogs/current")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_list_current_catalogs__bad_auth(full_database, bad_auth_client):
    response = bad_auth_client.get("/api/v1/catalogs/current")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_list_current_catalogs__noauth__public_get(
    full_database, fake_catalog_current, noauth_client, public_get
):
    response = noauth_client.get("/api/v1/catalogs/current")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]
    assert data["results"][0]["id"] == fake_catalog_current.id


def test_list_outdated_catalogs(full_database, fake_catalog_outdated, client):
    response = client.get("/api/v1/catalogs/outdated")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]
    assert data["results"][0]["id"] == fake_catalog_outdated.id


def test_list_outdated_catalogs__noauth(full_database, noauth_client):
    response = noauth_client.get("/api/v1/catalogs/outdated")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_list_outdated_catalogs__bad_auth(full_database, bad_auth_client):
    response = bad_auth_client.get("/api/v1/catalogs/outdated")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_list_outdated_catalogs__noauth__public_get(
    full_database, fake_catalog_outdated, noauth_client, public_get
):
    response = noauth_client.get("/api/v1/catalogs/outdated")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]
    assert data["results"][0]["id"] == fake_catalog_outdated.id


def test_get_catalog(fake_catalog, client):
    response = client.get(f"/api/v1/catalogs/{fake_catalog.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_catalog.id


def test_get_catalog__noauth(fake_catalog, noauth_client):
    response = noauth_client.get(f"/api/v1/catalogs/{fake_catalog.id}")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_catalog__bad_auth(fake_catalog, bad_auth_client):
    response = bad_auth_client.get(f"/api/v1/catalogs/{fake_catalog.id}")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_catalog__noauth__public_get(fake_catalog, noauth_client, public_get):
    response = noauth_client.get(f"/api/v1/catalogs/{fake_catalog.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_catalog.id


def test_get_catalog__not_found(client):
    response = client.get("/api/v1/catalogs/456")

    assert response.status_code == 404
    common.HTTPStatusError.model_validate(response.json())
    assert response.json() == {"detail": "Catalog not found"}


def test_get_catalog_page(fake_catalog, fake_page, client):
    response = client.get(
        f"/api/v1/catalogs/{fake_catalog.id}/pages/{fake_page.number}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_page.id


def test_get_catalog_page__noauth(fake_catalog, fake_page, noauth_client):
    response = noauth_client.get(
        f"/api/v1/catalogs/{fake_catalog.id}/pages/{fake_page.number}"
    )

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_catalog_page__bad_auth(fake_catalog, fake_page, bad_auth_client):
    response = bad_auth_client.get(
        f"/api/v1/catalogs/{fake_catalog.id}/pages/{fake_page.number}"
    )

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_catalog_page__noauth__public_get(
    fake_catalog, fake_page, noauth_client, public_get
):
    response = noauth_client.get(
        f"/api/v1/catalogs/{fake_catalog.id}/pages/{fake_page.number}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_page.id


def test_get_catalog_pages(fake_catalog, fake_page, client):
    response = client.get(f"/api/v1/catalogs/{fake_catalog.id}/pages")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == fake_page.id


def test_get_catalog_pages__noauth(fake_catalog, noauth_client):
    response = noauth_client.get(f"/api/v1/catalogs/{fake_catalog.id}/pages")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_catalog_pages__bad_auth(fake_catalog, bad_auth_client):
    response = bad_auth_client.get(f"/api/v1/catalogs/{fake_catalog.id}/pages")

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_catalog_pages__noauth__public_get(
    fake_catalog, fake_page, noauth_client, public_get
):
    response = noauth_client.get(f"/api/v1/catalogs/{fake_catalog.id}/pages")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == fake_page.id


def test_get_catalog_page__catalog_not_found(client):
    response = client.get("/api/v1/catalogs/234/pages/1")

    assert response.status_code == 404
    common.HTTPStatusError.model_validate(response.json())
    assert response.json() == {"detail": "Page not found"}


def test_get_catalog_page__page_not_found(client):
    response = client.get("/api/v1/catalogs/1/pages/780")

    assert response.status_code == 404
    common.HTTPStatusError.model_validate(response.json())
    assert response.json() == {"detail": "Page not found"}


def test_download_latest_provider_catalog__noauth(
    full_database, fake_provider, noauth_client
):
    response = noauth_client.get(
        f"/api/v1/catalogs/{fake_provider.id}/download",
    )

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_download_catalog(fake_catalog, full_database, client):
    response = client.get(
        f"/api/v1/catalogs/{fake_catalog.id}/download",
    )

    assert response.status_code == 200
    assert response.headers
    assert "content-type" in response.headers
    assert response.headers["content-type"] == "application/pdf"
    assert "content-disposition" in response.headers
    assert response.headers["content-disposition"].startswith("attachment")
    assert response.content
    pdf_reader = PdfReader(BytesIO(response.content), strict=True)
    assert len(pdf_reader.pages) == 1
    assert len(pdf_reader.pages[0].images) == 1


def test_download_catalog__noauth(full_database, fake_provider, noauth_client):
    response = noauth_client.get(
        f"/api/v1/catalogs/{fake_provider.id}/download",
    )

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_download_catalog__bad_auth(full_database, fake_provider, bad_auth_client):
    response = bad_auth_client.get(
        f"/api/v1/catalogs/{fake_provider.id}/download",
    )

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_download_catalog__not_found(full_database, client):
    response = client.get(
        "/api/v1/catalogs/546/download",
    )

    assert response.status_code == 404
    common.HTTPStatusError.model_validate(response.json())
    assert response.json()["detail"] == "Catalog not found"


def test_embed_catalog(fake_catalog, full_database, client):
    response = client.get(
        f"/api/v1/catalogs/{fake_catalog.id}/embed",
    )

    assert response.status_code == 200
    assert response.headers
    assert "content-type" in response.headers
    assert response.headers["content-type"] == "application/pdf"
    assert "content-disposition" in response.headers
    assert response.headers["content-disposition"].startswith("inline")
    assert response.content
    pdf_reader = PdfReader(BytesIO(response.content), strict=True)
    assert len(pdf_reader.pages) == 1
    assert len(pdf_reader.pages[0].images) == 1


def test_embed_catalog__noauth(full_database, fake_provider, noauth_client):
    response = noauth_client.get(
        f"/api/v1/catalogs/{fake_provider.id}/embed",
    )

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_embed_catalog__bad_auth(full_database, fake_provider, bad_auth_client):
    response = bad_auth_client.get(
        f"/api/v1/catalogs/{fake_provider.id}/embed",
    )

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_embed_catalog__not_found(full_database, client):
    response = client.get(
        "/api/v1/catalogs/546/embed",
    )

    assert response.status_code == 404
    common.HTTPStatusError.model_validate(response.json())
    assert response.json()["detail"] == "Catalog not found"


@pytest.mark.parametrize(("filename"), [None, "page_image.png"])
def test_download_catalog_page(fake_catalog, fake_page, fake_file, client, filename):
    response = client.get(
        urljoin(
            f"/api/v1/catalogs/{fake_catalog.id}/pages/{fake_page.number}/download",
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


def test_download_catalog_page__noauth(fake_catalog, fake_page, noauth_client):
    response = noauth_client.get(
        f"/api/v1/catalogs/{fake_catalog.id}/pages/{fake_page.number}/download"
    )

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_download_catalog_page__bad_auth(fake_catalog, fake_page, bad_auth_client):
    response = bad_auth_client.get(
        f"/api/v1/catalogs/{fake_catalog.id}/pages/{fake_page.number}/download"
    )

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_download_catalog_page__noauth__public_get(
    fake_catalog, fake_page, fake_file, noauth_client, public_get
):
    response = noauth_client.get(
        f"/api/v1/catalogs/{fake_catalog.id}/pages/{fake_page.number}/download"
    )

    assert response.status_code == 200
    assert response.content == fake_file.read_bytes()
    assert "content-disposition" in response.headers
    assert (
        response.headers["content-disposition"]
        == f'attachment; filename="{fake_file.name}"'
    )


def test_download_catalog_page__page_not_found(fake_catalog, client):
    response = client.get(f"/api/v1/catalogs/{fake_catalog.id}/pages/456/download")

    assert response.status_code == 404
    common.HTTPStatusError.model_validate(response.json())
    assert response.json() == {"detail": "Page not found"}


def test_download_catalog_page__catalog_not_found(client):
    response = client.get("/api/v1/catalogs/615/pages/1/download")

    assert response.status_code == 404
    common.HTTPStatusError.model_validate(response.json())
    assert response.json() == {"detail": "Page not found"}


@pytest.mark.parametrize(("filename"), [None, "page_image.png"])
def test_embed_catalog_page(fake_catalog, fake_page, fake_file, client, filename):
    response = client.get(
        urljoin(
            f"/api/v1/catalogs/{fake_catalog.id}/pages/{fake_page.number}/embed",
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


def test_embed_catalog_page__noauth(fake_catalog, fake_page, noauth_client):
    response = noauth_client.get(
        f"/api/v1/catalogs/{fake_catalog.id}/pages/{fake_page.number}/embed"
    )

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_embed_catalog_page__bad_auth(fake_catalog, fake_page, bad_auth_client):
    response = bad_auth_client.get(
        f"/api/v1/catalogs/{fake_catalog.id}/pages/{fake_page.number}/embed"
    )

    assert response.status_code == 401
    common.HTTPStatusError.model_validate(response.json())
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_embed_catalog_page__noauth__public_get(
    fake_catalog, fake_page, fake_file, noauth_client, public_get
):
    response = noauth_client.get(
        f"/api/v1/catalogs/{fake_catalog.id}/pages/{fake_page.number}/embed",
    )

    assert response.status_code == 200
    assert response.content == fake_file.read_bytes()
    assert "content-disposition" in response.headers
    assert (
        response.headers["content-disposition"]
        == f'inline; filename="{fake_file.name}"'
    )


def test_embed_catalog_page__page_not_found(fake_catalog, client):
    response = client.get(f"/api/v1/catalogs/{fake_catalog.id}/pages/456/embed")

    assert response.status_code == 404
    common.HTTPStatusError.model_validate(response.json())
    assert response.json() == {"detail": "Page not found"}


def test_embed_catalog_page__catalog_not_found(client):
    response = client.get("/api/v1/catalogs/615/pages/1/embed")

    assert response.status_code == 404
    common.HTTPStatusError.model_validate(response.json())
    assert response.json() == {"detail": "Page not found"}
