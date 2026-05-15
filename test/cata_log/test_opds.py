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

import xml.etree.ElementTree as ET
from io import BytesIO

from ebooklib import epub
from fastapi import status


def test_get_opds_catalog_overview(client, full_database):
    response = client.get("/opds/")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers
    assert "Content-Type" in response.headers
    assert response.headers["Content-Type"] == "application/atom+xml"
    content = response.content
    assert content
    xml_root = ET.fromstring(content)
    assert xml_root.tag == "{http://www.w3.org/2005/Atom}feed"
    entries = xml_root.findall("atom:entry", {"atom": "http://www.w3.org/2005/Atom"})
    assert entries
    links = xml_root.findall("atom:link", {"atom": "http://www.w3.org/2005/Atom"})
    assert links


def test_get_opds_catalog_overview__noauth(noauth_client, full_database):
    response = noauth_client.get("/opds/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_overview__bad_auth(bad_auth_client, full_database):
    response = bad_auth_client.get("/opds/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_latest(client, full_database):
    response = client.get("/opds/latest/")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers
    assert "Content-Type" in response.headers
    assert response.headers["Content-Type"] == "application/atom+xml"
    content = response.content
    assert content
    xml_root = ET.fromstring(content)
    assert xml_root.tag == "{http://www.w3.org/2005/Atom}feed"
    entries = xml_root.findall("atom:entry", {"atom": "http://www.w3.org/2005/Atom"})
    assert entries
    links = xml_root.findall("atom:link", {"atom": "http://www.w3.org/2005/Atom"})
    assert links


def test_get_opds_catalog_latest__noauth(noauth_client, full_database):
    response = noauth_client.get("/opds/latest/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_latest__bad_auth(bad_auth_client, full_database):
    response = bad_auth_client.get("/opds/latest/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_all(client, full_database):
    response = client.get("/opds/all/")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers
    assert "Content-Type" in response.headers
    assert response.headers["Content-Type"] == "application/atom+xml"
    content = response.content
    assert content
    xml_root = ET.fromstring(content)
    assert xml_root.tag == "{http://www.w3.org/2005/Atom}feed"
    entries = xml_root.findall("atom:entry", {"atom": "http://www.w3.org/2005/Atom"})
    assert entries
    links = xml_root.findall("atom:link", {"atom": "http://www.w3.org/2005/Atom"})
    assert links


def test_get_opds_catalog_all__noauth(noauth_client, full_database):
    response = noauth_client.get("/opds/all/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_all__bad_auth(bad_auth_client, full_database):
    response = bad_auth_client.get("/opds/all/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_current(client, full_database):
    response = client.get("/opds/current/")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers
    assert "Content-Type" in response.headers
    assert response.headers["Content-Type"] == "application/atom+xml"
    content = response.content
    assert content
    xml_root = ET.fromstring(content)
    assert xml_root.tag == "{http://www.w3.org/2005/Atom}feed"
    entries = xml_root.findall("atom:entry", {"atom": "http://www.w3.org/2005/Atom"})
    assert entries
    links = xml_root.findall("atom:link", {"atom": "http://www.w3.org/2005/Atom"})
    assert links


def test_get_opds_catalog_current__noauth(noauth_client, full_database):
    response = noauth_client.get("/opds/current/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_current__bad_auth(bad_auth_client, full_database):
    response = bad_auth_client.get("/opds/current/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_previews(client, full_database):
    response = client.get("/opds/previews/")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers
    assert "Content-Type" in response.headers
    assert response.headers["Content-Type"] == "application/atom+xml"
    content = response.content
    assert content
    xml_root = ET.fromstring(content)
    assert xml_root.tag == "{http://www.w3.org/2005/Atom}feed"
    entries = xml_root.findall("atom:entry", {"atom": "http://www.w3.org/2005/Atom"})
    assert entries
    links = xml_root.findall("atom:link", {"atom": "http://www.w3.org/2005/Atom"})
    assert links


def test_get_opds_catalog_previews__noauth(noauth_client, full_database):
    response = noauth_client.get("/opds/previews/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_previews__bad_auth(bad_auth_client, full_database):
    response = bad_auth_client.get("/opds/previews/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_outdated(client, full_database):
    response = client.get("/opds/outdated/")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers
    assert "Content-Type" in response.headers
    assert response.headers["Content-Type"] == "application/atom+xml"
    content = response.content
    assert content
    xml_root = ET.fromstring(content)
    assert xml_root.tag == "{http://www.w3.org/2005/Atom}feed"
    entries = xml_root.findall("atom:entry", {"atom": "http://www.w3.org/2005/Atom"})
    assert entries
    links = xml_root.findall("atom:link", {"atom": "http://www.w3.org/2005/Atom"})
    assert links


def test_get_opds_catalog_outdated__noauth(noauth_client, full_database):
    response = noauth_client.get("/opds/outdated/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_outdated__bad_auth(bad_auth_client, full_database):
    response = bad_auth_client.get("/opds/outdated/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_providers(client, full_database):
    response = client.get("/opds/providers/")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers
    assert "Content-Type" in response.headers
    assert response.headers["Content-Type"] == "application/atom+xml"
    content = response.content
    assert content
    xml_root = ET.fromstring(content)
    assert xml_root.tag == "{http://www.w3.org/2005/Atom}feed"
    entries = xml_root.findall("atom:entry", {"atom": "http://www.w3.org/2005/Atom"})
    assert entries
    links = xml_root.findall("atom:link", {"atom": "http://www.w3.org/2005/Atom"})
    assert links


def test_get_opds_catalog_providers__noauth(noauth_client, full_database):
    response = noauth_client.get("/opds/providers/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_providers__bad_auth(bad_auth_client, full_database):
    response = bad_auth_client.get("/opds/providers/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_provider(client, fake_provider, full_database):
    response = client.get(f"/opds/providers/{fake_provider.id}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers
    assert "Content-Type" in response.headers
    assert response.headers["Content-Type"] == "application/atom+xml"
    content = response.content
    assert content
    xml_root = ET.fromstring(content)
    assert xml_root.tag == "{http://www.w3.org/2005/Atom}feed"
    entries = xml_root.findall("atom:entry", {"atom": "http://www.w3.org/2005/Atom"})
    assert entries
    links = xml_root.findall("atom:link", {"atom": "http://www.w3.org/2005/Atom"})
    assert links


def test_get_opds_catalog_provider__noauth(noauth_client, fake_provider, full_database):
    response = noauth_client.get(f"/opds/providers/{fake_provider.id}/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_provider__bad_auth(
    bad_auth_client, fake_provider, full_database
):
    response = bad_auth_client.get(f"/opds/providers/{fake_provider.id}/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_catalog_epub(client, fake_catalog, fake_page, full_database):
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
    assert page_image.file_name == fake_page.file.name
    assert page_image.content == fake_page.file.path.read_bytes()
    page_chapter = book.get_item_with_href(f"chap_{fake_page.number + 1}.xhtml")
    assert page_chapter
    assert "img" in page_chapter.content.decode()
    assert f'src="{fake_page.file.name}"' in page_chapter.content.decode()


def test_get_catalog_epub__noauth(noauth_client, fake_catalog, full_database):
    response = noauth_client.get(f"/opds/{fake_catalog.id}.epub")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog___bad_auth(bad_auth_client, fake_catalog, full_database):
    response = bad_auth_client.get(f"/opds/{fake_catalog.id}.epub")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_get_opds_catalog_provider__not_found(client, full_database):
    response = client.get("/opds/215.epub")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Catalog not found"
