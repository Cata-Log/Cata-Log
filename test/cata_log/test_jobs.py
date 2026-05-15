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

from datetime import UTC, datetime, timedelta

import pytest

from cata_log import database, exceptions, jobs
from cata_log.constants import StatusEnum
from cata_log.settings import get_settings
from test.cata_log.conftest import SideEffects


@pytest.fixture(autouse=True)
def patch_database(patch_engine, patch_DBSession):
    """Patch the database."""


def test_fetch_provider__no_provider(db_session):
    jobs.fetch_provider(104)

    assert not db_session.query(database.Catalog).all()
    assert not db_session.query(database.Page).all()


@pytest.mark.parametrize(
    "side_effect",
    [
        SideEffects.DONOTHING,
    ],
)
def test_fetch_provider__success(db_session, fake_provider, side_effect):

    db_session.refresh(fake_provider)
    fake_provider.configuration = {
        **fake_provider.configuration,
        "side_effect": side_effect,
    }
    db_session.commit()

    jobs.fetch_provider(fake_provider.id)

    db_session.refresh(fake_provider)
    assert fake_provider.status == StatusEnum.HEALTHY
    assert len(fake_provider.catalogs) == 1
    assert len(fake_provider.catalogs[0].pages) == 10
    for page in fake_provider.catalogs[0].pages:
        assert page.file.path.read_bytes()


@pytest.mark.parametrize(
    "side_effect",
    [
        SideEffects.TRANSPORTERROR,
    ],
)
def test_fetch_provider__networkerror(db_session, fake_provider, side_effect):
    fake_provider.configuration = {
        **fake_provider.configuration,
        "side_effect": side_effect,
    }
    db_session.commit()
    with pytest.raises(exceptions.NetworkError):
        jobs.fetch_provider(fake_provider.id)


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
def test_fetch_provider__warning(
    db_session, fake_provider, side_effect, expected_warning
):
    fake_provider.configuration = {
        **fake_provider.configuration,
        "side_effect": side_effect,
    }
    db_session.commit()

    jobs.fetch_provider(fake_provider.id)

    db_session.refresh(fake_provider)
    assert fake_provider.status == expected_warning.provider_status
    assert not fake_provider.catalogs


def test_cleanup_catalogs(db_session, fake_catalog, fake_catalog_outdated):
    fake_catalog_outdated.created_at = datetime.now(tz=UTC) - timedelta(weeks=10)
    db_session.commit()

    assert len(db_session.query(database.Catalog).all()) == 2

    jobs.cleanup_catalogs()

    assert len(db_session.query(database.Catalog).all()) == 1
    assert db_session.get(database.Catalog, fake_catalog.id)


def test_cleanup_catalogs__no_expiration(
    monkeypatch, db_session, fake_catalog, fake_catalog_outdated
):
    monkeypatch.setenv("CATA_LOG_EXPIRATION_DAYS", "0")
    get_settings.cache_clear()
    fake_catalog_outdated.created_at = datetime.now(tz=UTC) - timedelta(weeks=100)
    db_session.commit()

    assert len(db_session.query(database.Catalog).all()) == 2

    jobs.cleanup_catalogs()

    assert len(db_session.query(database.Catalog).all()) == 2
    assert db_session.get(database.Catalog, fake_catalog.id)


def test_cleanup_storage(faker, fake_pagefile):
    (get_settings().storage_path / "unused_file").write_text(faker.text())
    assert fake_pagefile.path.exists()

    jobs.cleanup_storage()

    assert not (get_settings().storage_path / "unused_file").exists()
    assert fake_pagefile.path.exists()
