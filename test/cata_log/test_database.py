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

from cata_log import database
from cata_log.constants import STORAGE_PATH
from cata_log.providers import AldiSued


def test_Config_insertion(LocalSession):
    with LocalSession() as db_session:
        config = database.Config(name="testkey", value="testvalue")
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        assert config.id
        assert config.name == "testkey"
        assert config.value == "testvalue"
        assert config.created_at
        assert config.updated_at


def test_Provider_insertion(LocalSession):
    with LocalSession() as db_session:
        provider = database.Provider(class_id=AldiSued.id(), config={})
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        assert provider.id
        assert provider.class_id == AldiSued.id()
        assert provider.config == {}
        assert provider.task_id
        periodic_task = (
            db_session.query(PeriodicTask)
            .filter(PeriodicTask.id == provider.task_id)
            .one_or_none()
        )
        assert periodic_task
        assert periodic_task.task == "cata_log.tasks.fetch_catalog"
        assert periodic_task.args == f"[{provider.id}]"
        assert periodic_task.enabled is True
        assert periodic_task.crontab.minute == str(AldiSued.schedule._orig_minute)
        assert periodic_task.crontab.hour == str(AldiSued.schedule._orig_hour)
        assert periodic_task.crontab.day_of_month == str(
            AldiSued.schedule._orig_day_of_month
        )
        assert periodic_task.crontab.month_of_year == str(
            AldiSued.schedule._orig_month_of_year
        )
        assert periodic_task.crontab.day_of_week == str(
            AldiSued.schedule._orig_day_of_week
        )
        assert provider.created_at
        assert provider.updated_at


def test_Provider_deletion(db_session, full_database, fake_provider):
    assert len(db_session.query(database.Catalog).all()) == 3
    assert len(db_session.query(PeriodicTask).all()) == 1

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


def test_Catalog_deletion(db_session, full_database, fake_catalog):
    assert len(db_session.query(database.Catalog).all()) == 3

    db_session.delete(fake_catalog)
    db_session.commit()

    assert len(db_session.query(database.Catalog).all()) == 2
    assert not db_session.query(database.Page).all()


def test_Page_insertion(LocalSession, fake_catalog):
    with LocalSession() as db_session:
        page = database.Page(
            number=4,
            storage_path=str(STORAGE_PATH / "testfile.jpg"),
            catalog_id=fake_catalog.id,
        )
        db_session.add(page)
        db_session.commit()
        db_session.refresh(page)

        assert page.id
        assert page.number == 4
        assert page.storage_path == str(STORAGE_PATH / "testfile.jpg")
        assert page.catalog.id == fake_catalog.id
        assert page.catalog.valid_since == fake_catalog.valid_since
        assert len(fake_catalog.pages) == 1
        assert fake_catalog.pages[0].id == page.id
        assert fake_catalog.pages[0].number == page.number
        assert page.created_at
        assert page.updated_at


def test_Page_unique_together_constraint(faker, LocalSession, fake_page):
    with LocalSession() as db_session:
        db_session.add(
            database.Page(
                number=fake_page.number,
                catalog_id=fake_page.catalog_id,
                storage_path=faker.file_path(),
            )
        )

        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.flush()


def test_Page_deletion(db_session, fake_page_file, fake_page):
    assert fake_page_file.exists()

    db_session.delete(fake_page)
    db_session.commit()

    assert not fake_page_file.exists()
