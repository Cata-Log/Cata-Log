import os

import pytest

from cata_log.exceptions import ApplicationMisconfiguredError
from cata_log.settings import Settings


@pytest.fixture
def fake_setting(faker):
    fake_max_bytes = faker.random.randint(0, 1000000)
    os.environ["LOG_FILE_MAXSIZE"] = str(fake_max_bytes)
    yield fake_max_bytes
    del os.environ["LOG_FILE_MAXSIZE"]


@pytest.fixture
def fake_bad_setting(faker):
    fake_max_bytes = faker.word()
    os.environ["LOG_FILE_MAXSIZE"] = fake_max_bytes
    yield fake_max_bytes
    del os.environ["LOG_FILE_MAXSIZE"]


def test_Settings_value__from_env(fake_setting):
    result = Settings.LOG_FILE_MAXSIZE.value

    assert isinstance(result, int)
    assert result == fake_setting


def test_Settings_value__from_defaults():
    assert "LOG_FILE_MAXSIXE" not in os.environ

    result = Settings.LOG_FILE_MAXSIZE.value

    assert isinstance(result, int)


def test_Settings_bad_value(fake_bad_setting):
    with pytest.raises(ValueError, match=r"int()"):
        _ = Settings.LOG_FILE_MAXSIZE.value


def test_Settings_check__success(fake_setting):
    Settings.check()


def test_Settings_check__failure(fake_bad_setting):
    with pytest.raises(ApplicationMisconfiguredError):
        Settings.check()
