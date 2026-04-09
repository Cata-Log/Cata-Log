from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from freezegun import freeze_time

from cata_log import database, exceptions, tasks
from cata_log.constants import STORAGE_PATH, StatusEnum
from test.cata_log.conftest import SideEffects


@pytest.fixture(autouse=True)
def patch_database(patch_engine, patch_DBSession):
    """Patch the database."""


def test_fetch_provider__no_provider(db_session):
    tasks.fetch_provider(104)

    assert not db_session.query(database.Catalog).all()
    assert not db_session.query(database.Page).all()


@pytest.mark.parametrize(
    "side_effect",
    [
        SideEffects.DONOTHING,
    ],
)
def test_fetch_provider__success(db_session, fake_fs, fake_provider, side_effect):

    db_session.refresh(fake_provider)
    fake_provider.config = {**fake_provider.config, "side_effect": side_effect}
    db_session.commit()

    tasks.fetch_provider(fake_provider.id)

    db_session.refresh(fake_provider)
    assert fake_provider.status == StatusEnum.HEALTHY
    assert len(fake_provider.catalogs) == 1
    assert len(fake_provider.catalogs[0].pages) == 10
    for page in fake_provider.catalogs[0].pages:
        with page.storage_path.open() as page_file:
            assert page_file.read()


@pytest.mark.parametrize(
    "side_effect",
    [
        SideEffects.TRANSPORTERROR,
    ],
)
def test_fetch_provider__networkerror(db_session, fake_provider, side_effect):
    fake_provider.config = {**fake_provider.config, "side_effect": side_effect}
    db_session.commit()
    with pytest.raises(exceptions.NetworkError):
        tasks.fetch_provider(fake_provider.id)


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
    fake_provider.config = {**fake_provider.config, "side_effect": side_effect}
    db_session.commit()

    tasks.fetch_provider(fake_provider.id)

    db_session.refresh(fake_provider)
    assert fake_provider.status == expected_warning.provider_status
    assert not fake_provider.catalogs


def test_cleanup_catalogs(db_session, fake_catalog, fake_catalog_outdated):
    fake_catalog_outdated.created_at = datetime.now(tz=UTC) - timedelta(weeks=10)
    db_session.commit()

    assert len(db_session.query(database.Catalog).all()) == 2

    tasks.cleanup_catalogs()

    assert len(db_session.query(database.Catalog).all()) == 1
    assert db_session.get(database.Catalog, fake_catalog.id)


def test_cleanup_storage(faker, fake_fs, fake_page):
    (STORAGE_PATH / "unused_file").write_text(faker.text())
    assert fake_page.storage_path.exists()

    tasks.cleanup_storage()

    assert not (STORAGE_PATH / "unused_file").exists()
    assert fake_page.storage_path.exists()
