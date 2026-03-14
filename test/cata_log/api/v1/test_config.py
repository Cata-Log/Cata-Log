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
from cata_log.constants import DefaultConfig


def test_list_config(fake_config, client):
    response = client.get("api/v1/config")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]
    assert data[0]["name"] == fake_config.name


def test_list_config_defaults(client):
    response = client.get("api/v1/config/defaults")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(DefaultConfig)
    assert data[0]
    assert data[0]["name"]
    assert data[0]["value"] == getattr(DefaultConfig, data[0]["name"])


def test_get_config(fake_config, client):
    response = client.get(f"/api/v1/config/{fake_config.name}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == fake_config.name
    assert data["value"] == fake_config.value


def test_get_config__not_found(client):
    response = client.get("/api/v1/config/nf")

    assert response.status_code == 404
    assert response.json() == {"detail": "Config not found"}


def test_post_config(faker, LocalSession, client):
    config_json = {"name": faker.word(), "value": faker.word()}
    db_session = LocalSession()

    assert not db_session.query(database.Config).all()

    response = client.post("/api/v1/config", json=config_json)

    assert response.status_code == 201
    assert response.json() == config_json
    assert len(db_session.query(database.Config).all()) == 1
    config = (
        db_session.query(database.Config)
        .filter(database.Config.name == config_json["name"])
        .one_or_none()
    )
    assert config
    assert config.value == config_json["value"]


def test_post_config__duplicate(LocalSession, client, fake_config):
    config_json = {"name": fake_config.name, "value": "something"}
    db_session = LocalSession()

    response = client.post("/api/v1/config", json=config_json)

    assert response.status_code == 400
    assert len(db_session.query(database.Config).all()) == 1


def test_put_config(faker, fake_config, client):
    config_json = {"value": faker.word()}

    response = client.put(f"/api/v1/config/{fake_config.name}", json=config_json)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == fake_config.name
    assert data["value"] == config_json["value"]


def test_put_config__not_found(client):
    config_json = {"value": "something"}

    response = client.put("/api/v1/config/nf", json=config_json)

    assert response.status_code == 404
    assert response.json() == {"detail": "Config not found"}


def test_patch_config(faker, fake_config, client):
    config_json = {"value": faker.word()}

    response = client.patch(f"/api/v1/config/{fake_config.name}", json=config_json)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == fake_config.name
    assert data["value"] == config_json["value"]


def test_patch_config__not_found(client):
    config_json = {"value": "something"}

    response = client.patch("/api/v1/config/nf", json=config_json)

    assert response.status_code == 404
    assert response.json() == {"detail": "Config not found"}


def test_delete_config(fake_config, client):
    response = client.delete(f"/api/v1/config/{fake_config.name}")

    assert response.status_code == 204


def test_delete_config__not_found(client):
    response = client.delete("/api/v1/config/nf")

    assert response.status_code == 404
    assert response.json() == {"detail": "Config not found"}
