import os

import pytest
from pydantic import ValidationError

from cata_log.settings import get_settings


@pytest.fixture
def fake_setting(faker):
    fake_max_bytes = faker.random.randint(0, 1000000)
    os.environ["CATA_LOG_LOG_FILE_MAXSIZE"] = str(fake_max_bytes)
    yield fake_max_bytes
    del os.environ["CATA_LOG_LOG_FILE_MAXSIZE"]


@pytest.fixture
def fake_bad_setting(faker, monkeypatch):
    fake_max_bytes = faker.word()
    monkeypatch.setenv("CATA_LOG_LOG_FILE_MAXSIZE", fake_max_bytes)
    get_settings.cache_clear()


def test_Settings_value__from_env(fake_setting):
    result = get_settings().log_file_maxsize

    assert isinstance(result, int)
    assert result == fake_setting


def test_Settings_value__from_defaults():
    assert "CATA_LOG_LOG_FILE_MAXSIXE" not in os.environ

    result = get_settings().log_file_maxsize

    assert isinstance(result, int)


def test_settings_bad(fake_bad_setting):
    with pytest.raises(ValidationError):
        _ = get_settings().log_file_maxsize
