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

import pytest
from ebooklib import epub
from fastapi import status


@pytest.fixture(autouse=True)
def patch_database(patch_engine, patch_DBSession):
    """Patch the database."""


def test_get_opds_catalog_overview(client, fake_catalog, fake_page):
    response = client.get("/opds/")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers
    assert "Content-Type" in response.headers
    assert response.headers["Content-Type"] == "application/atom+xml"
    content = response.content.decode()
    assert content
    assert content.startswith("""<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:opds="http://opds-spec.org/2010/catalog">""")
    assert content.endswith("</feed>")
    assert "<entry>" in content
    assert "</entry>" in content


def test_get_opds_catalog_overview__noauth(noauth_client, fake_catalog, fake_page):
    response = noauth_client.get("/opds/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_overview__bad_auth(bad_auth_client, fake_catalog, fake_page):
    response = bad_auth_client.get("/opds/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_catalog_epub(client, fake_catalog, fake_page):
    response = client.get(f"/opds/{fake_catalog.id}.epub")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers
    assert "Content-Type" in response.headers
    assert response.headers["Content-Type"] == "application/epub+zip"
    content = response.content
    assert content
    book = epub.read_epub(BytesIO(content))
    assert book.get_metadata("DC", "title")
    assert book.get_metadata("DC", "identifier")
    assert book.get_metadata("DC", "creator")
    assert book.get_metadata("DC", "language")
    assert book.toc
    assert book.spine
    page_image = book.get_item_with_id(str(fake_page.id))
    assert page_image
    assert page_image.file_name == fake_page.file_name
    assert page_image.content == fake_page.storage_path.read_bytes()
    page_chapter = book.get_item_with_href(f"chap_{fake_page.number + 1}.xhtml")
    assert page_chapter
    assert "img" in page_chapter.content.decode()
    assert f'src="{fake_page.file_name}"' in page_chapter.content.decode()


def test_get_catalog_epub__noauth(noauth_client, fake_catalog, fake_page):
    response = noauth_client.get(f"/opds/{fake_catalog.id}.epub")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog___bad_auth(bad_auth_client, fake_catalog, fake_page):
    response = bad_auth_client.get(f"/opds/{fake_catalog.id}.epub")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"
