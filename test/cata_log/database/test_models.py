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

import pytest
import sqlalchemy.exc
from celery_sqlalchemy_v2_scheduler.models import PeriodicTask
from sqlalchemy.sql import text

from cata_log import database, exceptions
from cata_log.constants import STORAGE_PATH, StatusEnum
from test.cata_log.conftest import SideEffects


def test_Provider_insertion(LocalSession, provider_test_class):
    with LocalSession() as db_session:
        provider = database.Provider(
            class_id=provider_test_class.id(),
            config=dict(provider_test_class.default_config),
        )
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        assert provider.id
        assert provider.class_id == provider_test_class.id()
        assert provider.config == provider_test_class.default_config
        assert provider.task_id
        periodic_task = db_session.get(PeriodicTask, provider.task_id)
        assert periodic_task
        assert periodic_task.task == "cata_log.tasks.fetch_provider"
        assert periodic_task.args == f"[{provider.id}]"
        assert periodic_task.enabled is True
        assert periodic_task.crontab.minute == str(
            provider_test_class.schedule._orig_minute
        )
        assert periodic_task.crontab.hour == str(
            provider_test_class.schedule._orig_hour
        )
        assert periodic_task.crontab.day_of_month == str(
            provider_test_class.schedule._orig_day_of_month
        )
        assert periodic_task.crontab.month_of_year == str(
            provider_test_class.schedule._orig_month_of_year
        )
        assert periodic_task.crontab.day_of_week == str(
            provider_test_class.schedule._orig_day_of_week
        )
        assert provider.created_at
        assert provider.updated_at


def test_Provider_deletion(db_session, full_database, fake_provider):
    assert db_session.query(database.Catalog).all()
    assert db_session.query(PeriodicTask).all()
    assert db_session.query(database.Page).all()

    db_session.delete(fake_provider)
    db_session.commit()

    assert not db_session.query(database.Provider).all()
    assert not db_session.query(PeriodicTask).all()
    assert not db_session.query(database.Catalog).all()
    assert not db_session.query(database.Page).all()


def test_Provider_unique_together_constraint(LocalSession, fake_provider):
    with LocalSession() as db_session:
        db_session.add(
            database.Provider(
                class_id=fake_provider.class_id,
                config=fake_provider.config,
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
def test_Provider_fetch_catalog__success(
    db_session, fake_fs, fake_provider, side_effect
):
    fake_provider.config = {**fake_provider.config, "side_effect": side_effect}
    db_session.commit()

    fake_provider.fetch_catalog(db_session)

    db_session.refresh(fake_provider)
    assert fake_provider.status == StatusEnum.HEALTHY
    assert len(fake_provider.catalogs) == 1
    assert len(fake_provider.catalogs[0].pages) == 10
    for page in fake_provider.catalogs[0].pages:
        with page.file.path.open() as page_file:
            assert page_file.read()


@pytest.mark.parametrize(
    "side_effect",
    [
        SideEffects.TRANSPORTERROR,
    ],
)
def test_Provider_fetch_catalog__networkerror(db_session, fake_provider, side_effect):
    fake_provider.config = {**fake_provider.config, "side_effect": side_effect}
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
    fake_provider.config = {**fake_provider.config, "side_effect": side_effect}
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
        assert catalog.provider.class_id == fake_provider.class_id
        assert catalog.provider.config == fake_provider.config
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
            path=STORAGE_PATH / "testfile.jpg",
            sha256=faker.sha256(),
        )
        db_session.add(pagefile)
        db_session.commit()
        db_session.refresh(pagefile)

        assert pagefile.id
        assert pagefile.sha256
        assert pagefile.path == STORAGE_PATH / "testfile.jpg"
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
