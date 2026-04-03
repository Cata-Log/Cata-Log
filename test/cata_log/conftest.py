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

import base64
import enum
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import override

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from httpx import HTTPStatusError, Request, Response, TransportError
from pyfakefs.fake_filesystem_unittest import Patcher
from sqlalchemy import StaticPool, create_engine, orm

from cata_log import constants, database, exceptions
from cata_log.providers import Provider
from cata_log.providers.configuration import Configuration
from cata_log.providers.regions import Germany


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.ModelBase.metadata.create_all(engine)
    try:
        yield engine
    finally:
        database.ModelBase.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def LocalSession(engine):
    return orm.sessionmaker(bind=engine)


@pytest.fixture
def patch_engine(monkeypatch, engine):
    monkeypatch.setattr("cata_log.database.engine", engine)


@pytest.fixture
def patch_DBSession(monkeypatch, LocalSession):
    monkeypatch.setattr("cata_log.database.DBSession", LocalSession)


@pytest.fixture
def db_session(LocalSession):
    with LocalSession() as db_session:
        yield db_session


@pytest.fixture(autouse=True)
def fake_credentials(faker):
    os.environ["USERNAME"] = faker.user_name()
    os.environ["PASSWORD"] = faker.password()


@pytest.fixture
def fake_credentials_encoded():
    username = os.environ["USERNAME"]
    password = os.environ["PASSWORD"]
    return base64.b64encode(f"{username}:{password}".encode()).decode("utf-8")


@pytest.fixture
def noauth_client(fake_fs):
    from cata_log.main import app  # noqa: PLC0415

    return TestClient(app)


@pytest.fixture
def bad_auth_client(faker, noauth_client):
    noauth_client.headers = {"Authorization": f"Basic {faker.word()}"}
    return noauth_client


@pytest.fixture
def client(fake_credentials_encoded, noauth_client):
    noauth_client.headers = {"Authorization": f"Basic {fake_credentials_encoded}"}
    return noauth_client


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
        patcher.fs.add_real_directory(Path(constants.__file__).parent)
        patcher.fs.add_real_file("pyproject.toml")
        patcher.fs.add_real_directory(
            "src/cata_log/web/static/js", target_path="/opt/cata_log/web/static/js"
        )
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
def fake_page(faker, db_session, fake_catalog_preview, fake_page_file):
    fake_page = database.Page(
        number=0,
        catalog_id=fake_catalog_preview.id,
        storage_path=str(fake_page_file),
        sha256=faker.sha256(),
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


class SideEffects(enum.StrEnum):
    DONOTHING = "donothing"
    HTTP_400 = "400"
    HTTP_404 = "404"
    HTTP_500 = "500"
    TRANSPORTERROR = "transporterror"
    KEYERROR = "keyerror"
    VALUEERROR = "valueerror"
    EXCEPTION = "exception"
    PAGESEXHAUSTED = "pagesexhausted"
    CATALOGUNAVAILABLE = "catalogunavailable"

    @classmethod
    def run(cls, side_effect):
        match side_effect:
            case cls.HTTP_400:
                raise HTTPStatusError(
                    message="",
                    request=Request(method="GET", url="https://test-error.it"),
                    response=Response(status_code=400),
                )
            case cls.HTTP_404:
                raise HTTPStatusError(
                    message="",
                    request=Request(method="GET", url="https://test-error.it"),
                    response=Response(status_code=404),
                )
            case cls.HTTP_500:
                raise HTTPStatusError(
                    message="",
                    request=Request(method="GET", url="https://test-error.it"),
                    response=Response(status_code=500),
                )
            case cls.TRANSPORTERROR:
                raise TransportError(message="")
            case cls.VALUEERROR:
                raise ValueError
            case cls.KEYERROR:
                raise KeyError
            case cls.EXCEPTION:
                raise Exception  # noqa: TRY002  # test for the most generic exception
            case cls.PAGESEXHAUSTED:
                raise exceptions.PagesExhausted
            case cls.CATALOGUNAVAILABLE:
                raise exceptions.CatalogUnavailableWarning
            case _:
                return


@pytest.fixture(scope="session")
def test_provider_class(_session_faker):  # noqa: PT019 # simplifies things
    class TestProvider(Provider):
        name = "test-provider"
        description = "A provider for testing"
        url = "https://test.provider.it/catalog"
        region = Germany
        first_page_number = 0
        configuration = (
            Configuration(
                name="side_effect",
                helptext="set the side effect of a method execution",
                default=SideEffects.DONOTHING,
            ),
            Configuration(
                name="pass_get_catalog_data",
                helptext="whether to pass in _get_catalog_data",
                default="",
                parse_as=bool,
            ),
            Configuration(
                name="required_config", helptext="helptext for required config"
            ),
            Configuration(
                name="optional_config",
                helptext="helptext for optional config",
                default="default_config",
            ),
            Configuration(
                name="typed_config", helptext="helptext for typed config", parse_as=int
            ),
            Configuration(
                name="optional_typed_config",
                helptext="helptext for typed optional config",
                default="14.5",
                parse_as=float,
            ),
        )

        @override
        def _get_page(self, page_number):
            SideEffects.run(self._config["side_effect"])
            return _session_faker.text().encode()

        @override
        def _get_catalog_data(self):
            if self._config["pass_get_catalog_data"]:
                return
            SideEffects.run(self._config["side_effect"])

        @override
        def _get_valid_since(self):
            SideEffects.run(self._config["side_effect"])
            return _session_faker.date_time()

        @override
        def _get_valid_until(self):
            SideEffects.run(self._config["side_effect"])
            return self._get_valid_since() + _session_faker.time_delta()

    return TestProvider


@pytest.fixture(scope="session")
def default_test_provider_config(test_provider_class):
    return {
        config.name: "1"
        for config in test_provider_class.configuration
        if config.default is None
    }
