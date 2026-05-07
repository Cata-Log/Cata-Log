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
from types import MappingProxyType
from typing import override

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from httpx import HTTPStatusError, Request, Response, TransportError
from pyfakefs.fake_filesystem_unittest import Patcher
from sqlalchemy import StaticPool, create_engine, orm

from cata_log import constants, database, exceptions
from cata_log.exceptions import PagesExhausted
from cata_log.providers import Provider
from cata_log.providers.base import Preview
from cata_log.providers.configuration import Configuration
from cata_log.providers.regions import Germany
from cata_log.settings import settings


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


@pytest.fixture
def fake_username(faker):
    fake_username = faker.user_name()
    os.environ["USERNAME"] = fake_username
    yield fake_username
    del os.environ["USERNAME"]


@pytest.fixture
def fake_password(faker):
    fake_password = faker.password()
    os.environ["PASSWORD"] = fake_password
    yield fake_password
    del os.environ["PASSWORD"]


@pytest.fixture
def fake_credentials(fake_username, fake_password):
    return fake_username, fake_password


@pytest.fixture
def fake_credentials_encoded(fake_credentials):
    username, password = fake_credentials
    return base64.b64encode(f"{username}:{password}".encode()).decode("utf-8")


@pytest.fixture
def public_get():
    os.environ["PUBLIC_GET"] = "true"
    yield
    del os.environ["PUBLIC_GET"]


@pytest.fixture
def fastapi_app(fake_fs):
    from cata_log.main import app  # noqa: PLC0415

    yield app

    del app


@pytest.fixture
def noauth_client(fake_credentials, fastapi_app):
    with TestClient(fastapi_app) as noauth_client:
        yield noauth_client


@pytest.fixture
def bad_auth_client(faker, noauth_client):
    noauth_client.headers = {"Authorization": f"Basic {faker.word()}"}
    return noauth_client


@pytest.fixture
def client(fake_credentials_encoded, noauth_client):
    noauth_client.headers = {"Authorization": f"Basic {fake_credentials_encoded}"}
    return noauth_client


@pytest.fixture
def fake_fs(monkeypatch):
    """A mock Linux filesystem for realistic testing.

    Contains directories at the STORAGE_PATH and LOG_DIRECTORY_PATH.
    """
    with Patcher() as patcher:
        if not patcher.fs:
            raise OSError("Generator could not create a fakefs!")

        patcher.fs.create_dir(constants.STORAGE_PATH)
        monkeypatch.setattr(
            "cata_log.constants.STORAGE_PATH", Path(str(settings.storage_path))
        )
        patcher.fs.create_dir(settings.logs_path)
        patcher.fs.add_real_directory(Path(constants.__file__).parent.parent.parent)
        patcher.fs.add_real_directory(
            Path(constants.__file__).parent, target_path="/opt/cata_log"
        )
        patcher.fs.add_real_file("pyproject.toml")
        yield patcher.fs


@pytest.fixture
def fake_provider(db_session, provider_test_class):
    fake_provider = database.Provider(
        class_uid=provider_test_class.uid,
        configuration=provider_test_class.validate_configuration(
            provider_test_class.default_configuration
        ),
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
def fake_file(faker, fake_fs):
    path = constants.STORAGE_PATH / "0.jpg"
    path.write_text(faker.text())
    return path


@pytest.fixture
def fake_pagefile(faker, db_session, fake_file):
    fake_pagefile = database.PageFile(
        path=str(fake_file), size=faker.random.randint(1, 1000), sha256=faker.sha256()
    )
    db_session.add(fake_pagefile)
    db_session.commit()
    db_session.refresh(fake_pagefile)
    return fake_pagefile


@pytest.fixture
def fake_page(db_session, fake_catalog_preview, fake_pagefile):
    fake_page = database.Page(
        number=0, catalog_id=fake_catalog_preview.id, file_id=fake_pagefile.id
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
def provider_test_class(_session_faker):
    class TestProvider(Provider):
        uid = "test-provider-de"
        name = "Test-Provider"
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
        default_configuration = MappingProxyType(
            {config.name: "1" for config in configuration if config.default is None}
        )

        @override
        def _get_page(self, page_number):
            SideEffects.run(self._configuration["side_effect"])
            if page_number >= 10:
                raise PagesExhausted
            return _session_faker.text().encode()

        @override
        def _get_catalog_data(self):
            if self._configuration["pass_get_catalog_data"]:
                return
            SideEffects.run(self._configuration["side_effect"])

        @override
        def _get_valid_since(self):
            SideEffects.run(self._configuration["side_effect"])
            return _session_faker.date_time()

        @override
        def _get_valid_until(self):
            SideEffects.run(self._configuration["side_effect"])
            return self._get_valid_since() + _session_faker.time_delta()

    return TestProvider


@pytest.fixture(scope="session")
def preview_provider_test_class(provider_test_class):
    class TestPreviewProvider(Preview, provider_test_class):
        uid = provider_test_class.uid + "-preview"
        name = provider_test_class.name + "-Preview"
        preview_timedelta = timedelta(days=7)

    return TestPreviewProvider
