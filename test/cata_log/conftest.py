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

import os
from datetime import UTC, datetime, timedelta

import pytest
from freezegun import freeze_time
from pyfakefs.fake_filesystem_unittest import Patcher
from sqlalchemy import StaticPool, create_engine, orm

from cata_log import constants, database


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.ModelBase.metadata.create_all(engine)
    yield engine
    database.ModelBase.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def LocalSession(engine):
    return orm.sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def patch_DBSession(monkeypatch, LocalSession):
    monkeypatch.setattr("cata_log.database.DBSession", LocalSession)


@pytest.fixture
def db_session(LocalSession):
    with LocalSession() as db_session:
        yield db_session


@pytest.fixture
def fake_fs():
    """A mock Linux filesystem for realistic testing.

    Contains directories at the STORAGE_PATH and LOG_DIRECTORY_PATH.
    """
    with Patcher() as patcher:
        if not patcher.fs:
            raise OSError("Generator could not create a fakefs!")

        patcher.fs.create_dir(constants.STORAGE_PATH)
        patcher.fs.create_dir(constants.LOG_DIRECTORY_PATH)
        patcher.fs.add_real_directory(os.path.dirname(constants.__file__))
        patcher.fs.add_real_file("pyproject.toml")
        yield patcher.fs


@pytest.fixture
def fake_config(db_session):
    fake_config = database.Config(name="test_conf", value="test_val")
    db_session.add(fake_config)
    db_session.commit()
    db_session.refresh(fake_config)
    return fake_config


@pytest.fixture
def fake_provider(db_session):
    fake_provider = database.Provider(
        class_id="rewe-deutschland", config={"markt_id": "rewe123"}
    )
    db_session.add(fake_provider)
    db_session.commit()
    db_session.refresh(fake_provider)
    return fake_provider


@pytest.fixture
def fake_catalog_current(db_session, fake_provider):
    now = datetime.now(tz=UTC) - timedelta(days=1)
    with freeze_time(now):
        fake_catalog = database.Catalog(
            valid_since=now - timedelta(days=3),
            valid_until=now + timedelta(days=4),
            provider_id=fake_provider.id,
        )
        db_session.add(fake_catalog)
        db_session.flush()
        fake_catalog.created_at = now
        fake_catalog.updated_at = now
        db_session.flush()
    db_session.commit()
    db_session.refresh(fake_catalog)
    return fake_catalog


@pytest.fixture
def fake_catalog_outdated(db_session, fake_provider):
    now = datetime.now(tz=UTC) - timedelta(days=2)
    with freeze_time(now):
        fake_catalog = database.Catalog(
            valid_since=now - timedelta(days=8),
            valid_until=now - timedelta(days=1),
            provider_id=fake_provider.id,
        )
        db_session.add(fake_catalog)
        db_session.flush()
        fake_catalog.created_at = now
        fake_catalog.updated_at = now
        db_session.flush()
    db_session.commit()
    db_session.refresh(fake_catalog)
    return fake_catalog


@pytest.fixture
def fake_catalog_preview(db_session, fake_provider):
    now = datetime.now(tz=UTC)
    with freeze_time(now):
        fake_catalog = database.Catalog(
            valid_since=now + timedelta(days=2),
            valid_until=now + timedelta(days=9),
            provider_id=fake_provider.id,
        )
        db_session.add(fake_catalog)
        db_session.flush()
        fake_catalog.created_at = now
        fake_catalog.updated_at = now
        db_session.flush()
    db_session.commit()
    db_session.refresh(fake_catalog)
    return fake_catalog


@pytest.fixture
def fake_catalog(fake_catalog_preview):
    return fake_catalog_preview


@pytest.fixture
def fake_latest_catalog(fake_catalog_preview):
    return fake_catalog_preview


@pytest.fixture
def fake_page_file(faker, fake_fs):
    storage_path = constants.STORAGE_PATH / "0.jpg"
    with storage_path.open("wb") as fake_file:
        fake_file.write(faker.text().encode())
    return storage_path


@pytest.fixture
def fake_page(db_session, fake_catalog_preview, fake_page_file):
    fake_page = database.Page(
        number=0,
        catalog_id=fake_catalog_preview.id,
        storage_path=str(fake_page_file),
    )
    db_session.add(fake_page)
    db_session.commit()
    db_session.refresh(fake_page)
    return fake_page


@pytest.fixture
def full_database(
    fake_provider,
    fake_catalog_outdated,
    fake_catalog_current,
    fake_catalog_preview,
    fake_page,
):
    pass
