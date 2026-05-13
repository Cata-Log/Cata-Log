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
import sys
from io import BytesIO
from types import MappingProxyType

from PIL import Image

sys.argv = [
    "python3 -m cata_log",
]
os.environ["CATA_LOG_DATA_PATH"] = "/tmp/mnt/"
os.environ["CATA_LOG_STORAGE_PATH"] = "/tmp/mnt/storage/"
os.environ["CATA_LOG_DATABASE_PATH"] = "/tmp/mnt/db/"
os.environ["CATA_LOG_PLUGIN_PATH"] = "/tmp/mnt/plugins/"
os.environ["CATA_LOG_LOGS_PATH"] = "/tmp/var/log/cata-log/"

# ruff: noqa: E402 # must set environment before importing from cata_log
import base64
import enum
from datetime import UTC, datetime, timedelta
from typing import override

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from httpx import HTTPStatusError, Request, Response, TransportError
from pydantic import Field
from sqlalchemy import StaticPool, create_engine, orm

from cata_log import database, exceptions
from cata_log.exceptions import PagesExhausted
from cata_log.providers import Provider
from cata_log.providers.base import Preview
from cata_log.providers.regions import Germany
from cata_log.scheduler import scheduler
from cata_log.settings import get_settings


@pytest.fixture(autouse=True)
def temp_settings_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("CATA_LOG_DATA_PATH", str(tmp_path / "mnt/"))
    monkeypatch.setenv("CATA_LOG_STORAGE_PATH", str(tmp_path / "mnt/storage/"))
    monkeypatch.setenv("CATA_LOG_DATABASE_PATH", str(tmp_path / "mnt/db/"))
    monkeypatch.setenv("CATA_LOG_PLUGIN_PATH", str(tmp_path / "mnt/plugins/"))
    monkeypatch.setenv("CATA_LOG_LOGS_PATH", str(tmp_path / "var/log/cata-log/"))
    get_settings.cache_clear()


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
def started_scheduler():
    if not scheduler.running:
        scheduler.start()
    return scheduler


@pytest.fixture
def fake_username(monkeypatch, faker):
    fake_username = faker.user_name()
    monkeypatch.setenv("CATA_LOG_USERNAME", fake_username)
    get_settings.cache_clear()
    return fake_username


@pytest.fixture
def fake_password(monkeypatch, faker):
    fake_password = faker.password()
    monkeypatch.setenv("CATA_LOG_PASSWORD", fake_password)
    get_settings.cache_clear()
    return fake_password


@pytest.fixture
def fake_credentials(fake_username, fake_password):
    return fake_username, fake_password


@pytest.fixture
def fake_credentials_encoded(fake_credentials):
    username, password = fake_credentials
    return base64.b64encode(f"{username}:{password}".encode()).decode("utf-8")


@pytest.fixture
def public_get(monkeypatch):
    monkeypatch.setenv("CATA_LOG_PUBLIC_GET", "true")
    get_settings.cache_clear()


@pytest.fixture
def fastapi_app():
    from cata_log.app import app  # noqa: PLC0415

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
def fake_provider(db_session, provider_test_class):
    fake_provider = database.Provider(
        class_uid=provider_test_class.uid,
        configuration=provider_test_class.validate_configuration(
            provider_test_class.default_configuration
        ).model_dump(),
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
def fake_file(faker):
    path = get_settings().storage_path / "0.jpg"
    path.write_text(faker.text())
    return path


@pytest.fixture
def fake_pagefile(faker, db_session, fake_file):
    fake_pagefile = database.PageFile(
        path=str(fake_file),
        size=faker.random.randint(1, 1000),
        sha256=faker.sha256(),
        original_sha256=faker.sha256(),
        height=faker.random.randint(100, 1000),
        width=faker.random.randint(100, 1000),
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

        class Configuration(Provider.Configuration):
            side_effect: SideEffects = Field(
                default=SideEffects.DONOTHING,
                description="set the side effect of a method execution",
            )

            pass_get_catalog_data: bool = Field(
                default=False,
                description="whether to pass in _get_catalog_data",
            )

            required_config: str = Field(description="helptext for required config")

            optional_config: str = Field(
                default="default_config",
                description="helptext for optional config",
            )

            typed_config: int = Field(
                description="helptext for typed config",
            )

            optional_typed_config: float = Field(
                default=14.5,
                description="helptext for typed optional config",
            )

        default_configuration = MappingProxyType(
            {
                config_name: (config_field.annotation or str)("0")
                for config_name, config_field in Configuration.model_fields.items()
                if config_field.is_required()
            }
        )

        @override
        def _get_page(self, page_number):
            SideEffects.run(self._configuration.side_effect)
            if page_number >= 10:
                raise PagesExhausted
            with Image.new(
                mode="RGB", size=(10, 25), color=_session_faker.color()
            ) as fake_image:
                fake_image_bytes_io = BytesIO()
                fake_image.save(fake_image_bytes_io, format="JPEG")
            fake_image_bytes_io.seek(0)
            return fake_image_bytes_io.read()

        @override
        def _get_catalog_data(self):
            if self._configuration.pass_get_catalog_data:
                return
            SideEffects.run(self._configuration.side_effect)

        @override
        def _get_valid_since(self):
            SideEffects.run(self._configuration.side_effect)
            return _session_faker.date_time()

        @override
        def _get_valid_until(self):
            SideEffects.run(self._configuration.side_effect)
            return self._get_valid_since() + _session_faker.time_delta()

    return TestProvider


@pytest.fixture(scope="session")
def preview_provider_test_class(provider_test_class):
    class TestPreviewProvider(Preview, provider_test_class):
        uid = provider_test_class.uid + "-preview"
        name = provider_test_class.name + "-Preview"
        preview_timedelta = timedelta(days=7)

    return TestPreviewProvider
