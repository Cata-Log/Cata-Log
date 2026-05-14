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

from datetime import UTC, datetime
from hashlib import sha256

import pytest
import sqlalchemy.exc
from PIL import Image
from sqlalchemy.sql import text

from cata_log import database, exceptions
from cata_log.constants import StatusEnum
from cata_log.settings import get_settings
from test.cata_log.conftest import SideEffects


def test_sqlite_pragmas(LocalSession):
    with LocalSession() as db_session:
        assert db_session.execute(text("PRAGMA foreign_keys;")).scalar() == 1
        assert db_session.execute(text("PRAGMA busy_timeout;")).scalar() == 5000
        assert db_session.execute(text("PRAGMA synchronous;")).scalar() == 1


def test_Provider_insertion(LocalSession, started_scheduler, provider_test_class):
    with LocalSession() as db_session:
        provider = database.Provider(
            class_uid=provider_test_class.uid,
            configuration=dict(provider_test_class.default_configuration),
        )
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        assert provider.id
        assert provider.class_uid == provider_test_class.uid
        assert provider.configuration == provider_test_class.default_configuration
        assert provider.job_id
        job = started_scheduler.get_job(provider.job_id)
        assert job
        assert job.func.__name__ == "fetch_provider"
        assert len(job.args) == 1
        assert 1 in job.args
        assert provider.created_at
        assert provider.updated_at


def test_Provider_insertion__bad_class_uid(LocalSession):
    with LocalSession() as db_session:
        provider = database.Provider(
            class_uid="unknown1234",
            configuration={},
        )
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        assert provider.id
        assert provider.class_uid == "unknown1234"
        assert provider.configuration == {}
        assert not provider.job_id
        assert provider.created_at
        assert provider.updated_at


def test_Provider_deletion(db_session, full_database, fake_provider):
    pass


def test_Provider_unique_together_constraint(LocalSession, fake_provider):
    with LocalSession() as db_session:
        db_session.add(
            database.Provider(
                class_uid=fake_provider.class_uid,
                configuration=fake_provider.configuration,
            )
        )

        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.flush()


@pytest.mark.parametrize(
    "side_effect",
    [
        SideEffects.DONOTHING,
    ],
)
def test_Provider_fetch_catalog__success(db_session, fake_provider, side_effect):
    fake_provider.configuration["side_effect"] = side_effect
    db_session.commit()

    fake_provider.fetch_catalog(db_session)

    db_session.refresh(fake_provider)
    assert fake_provider.status == StatusEnum.HEALTHY
    assert len(fake_provider.catalogs) == 1
    assert len(fake_provider.catalogs[0].pages) == 10
    for page in fake_provider.catalogs[0].pages:
        assert page.file.sha256 == sha256(page.file.path.read_bytes()).hexdigest()
        with Image.open(page.file.path) as page_image:
            assert page_image.height == page.file.height
            assert page_image.width == page.file.width
            assert page_image.format == "WEBP"


@pytest.mark.parametrize(
    "side_effect",
    [
        SideEffects.TRANSPORTERROR,
    ],
)
def test_Provider_fetch_catalog__networkerror(db_session, fake_provider, side_effect):
    fake_provider.configuration = {
        **fake_provider.configuration,
        "side_effect": side_effect,
    }
    db_session.commit()
    with pytest.raises(exceptions.NetworkError):
        fake_provider.fetch_catalog(db_session)


@pytest.mark.parametrize(
    ("side_effect", "expected_warning"),
    [
        (SideEffects.HTTP_400, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_500, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_404, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.KEYERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.EXCEPTION, exceptions.ProviderBrokenWarning),
        (SideEffects.CATALOGUNAVAILABLE, exceptions.CatalogUnavailableWarning),
    ],
)
def test_Provider_fetch_catalog__warning(
    db_session, fake_provider, side_effect, expected_warning
):
    fake_provider.configuration = {
        **fake_provider.configuration,
        "side_effect": side_effect,
    }
    db_session.commit()

    fake_provider.fetch_catalog(db_session)

    db_session.refresh(fake_provider)
    assert fake_provider.status == expected_warning.provider_status
    assert not fake_provider.catalogs


def test_Catalog_insertion(LocalSession, fake_provider):
    with LocalSession() as db_session:
        catalog = database.Catalog(
            valid_since=datetime.now(tz=UTC),
            valid_until=datetime.now(tz=UTC),
            provider_id=fake_provider.id,
        )
        db_session.add(catalog)
        db_session.commit()
        db_session.refresh(catalog)

        assert catalog.id
        assert catalog.valid_since
        assert catalog.valid_until
        assert catalog.provider.id == fake_provider.id
        assert catalog.provider.class_uid == fake_provider.class_uid
        assert catalog.provider.configuration == fake_provider.configuration
        assert len(fake_provider.catalogs) == 1
        assert fake_provider.catalogs[0].id == catalog.id
        assert fake_provider.catalogs[0].valid_since == catalog.valid_since
        assert catalog.created_at
        assert catalog.updated_at


def test_Catalog_deletion(db_session, fake_catalog, full_database):
    assert len(db_session.query(database.Catalog).all()) == 3

    db_session.delete(fake_catalog)
    db_session.commit()

    assert len(db_session.query(database.Catalog).all()) == 2
    assert not db_session.query(database.Page).all()


def test_PageFile_insertion(faker, LocalSession):
    with LocalSession() as db_session:
        pagefile = database.PageFile(
            path=get_settings().storage_path / "testfile.jpg",
            sha256=faker.sha256(),
            original_sha256=faker.sha256(),
            size=faker.random.randint(1, 2000),
            width=faker.random.randint(100, 1000),
            height=faker.random.randint(100, 1000),
        )
        db_session.add(pagefile)
        db_session.commit()
        db_session.refresh(pagefile)

        assert pagefile.id
        assert pagefile.sha256
        assert pagefile.original_sha256
        assert pagefile.width
        assert pagefile.height
        assert pagefile.path == get_settings().storage_path / "testfile.jpg"
        assert pagefile.created_at
        assert pagefile.updated_at


def test_PageFile_deletion(db_session, fake_file, fake_pagefile):
    assert fake_file.exists()

    db_session.delete(fake_pagefile)
    db_session.commit()

    assert not fake_file.exists()


def test_PageFile_deletion__restricted(db_session, fake_file, fake_pagefile, fake_page):
    assert fake_file.exists()
    assert len(fake_pagefile.pages)

    db_session.delete(fake_pagefile)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError, match="FOREIGN KEY constraint failed"
    ):
        db_session.commit()

    assert fake_file.exists()


def test_Page_insertion(LocalSession, fake_catalog, fake_pagefile):
    with LocalSession() as db_session:
        page = database.Page(
            number=4,
            catalog_id=fake_catalog.id,
            file_id=fake_pagefile.id,
        )
        db_session.add(page)
        db_session.commit()
        db_session.refresh(page)

        assert page.id
        assert page.number == 4
        assert page.file.id == fake_pagefile.id
        assert len(fake_pagefile.pages) == 1
        assert fake_pagefile.pages[0].id == page.id
        assert page.catalog.id == fake_catalog.id
        assert page.catalog.valid_since == fake_catalog.valid_since
        assert len(fake_catalog.pages) == 1
        assert fake_catalog.pages[0].id == page.id
        assert fake_catalog.pages[0].number == page.number
        assert page.created_at
        assert page.updated_at


def test_Page_unique_together_constraint(LocalSession, fake_pagefile, fake_page):
    with LocalSession() as db_session:
        db_session.add(
            database.Page(
                number=fake_page.number,
                catalog_id=fake_page.catalog_id,
                file_id=fake_pagefile.id,
            )
        )

        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.flush()


def test_Page_deletion(db_session, fake_pagefile, fake_page):
    pagefile_id = fake_pagefile.id

    assert len(fake_pagefile.pages) == 1

    db_session.delete(fake_page)
    db_session.commit()

    assert not db_session.get(database.PageFile, pagefile_id)


def test_Page_deletion__remaining_pagefile_pages(
    faker, db_session, fake_pagefile, fake_page
):
    other_page = database.Page(
        number=faker.random.randint(0, 10),
        catalog_id=fake_page.catalog_id,
        file_id=fake_pagefile.id,
    )
    db_session.add(other_page)
    db_session.commit()
    pagefile_id = fake_pagefile.id

    assert len(fake_pagefile.pages) == 2

    db_session.delete(fake_page)
    db_session.commit()

    assert db_session.get(database.PageFile, pagefile_id)
    assert len(fake_pagefile.pages) == 1
