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


def test_static_pages(client, fake_page):
    response = client.get(f"/static/pages/{fake_page.file.path.name}")

    assert response.status_code == 200
    assert response.content == fake_page.file.path.read_bytes()


def test_static_pages__bad_auth(bad_auth_client, fake_page):
    response = bad_auth_client.get(f"/static/pages/{fake_page.file.path.name}")

    assert response.status_code == 200
    assert response.content == fake_page.file.path.read_bytes()


def test_static_pages__noauth(noauth_client, fake_page):
    response = noauth_client.get(f"/static/pages/{fake_page.file.path.name}")

    assert response.status_code == 200
    assert response.content == fake_page.file.path.read_bytes()


def test_static_js(client):
    response = client.get("/static/js/theme-switcher.js")

    assert response.status_code == 200
    assert response.content


def test_static_js__noauth(noauth_client):
    response = noauth_client.get("/static/js/theme-switcher.js")

    assert response.status_code == 200
    assert response.content


def test_static_js__bad_auth(bad_auth_client):
    response = bad_auth_client.get("/static/js/theme-switcher.js")

    assert response.status_code == 200
    assert response.content
