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

import logging
import logging.config

import pytest

from cata_log_hub.settings import get_settings


@pytest.fixture
def apply_logging_config():
    import cata_log_hub.logging  # noqa: PLC0415 # toplevel import messes up tmp_paths

    logging.config.dictConfig(cata_log_hub.logging.CATA_LOG_LOGGING_CONFIG)
    logging.config.dictConfig(cata_log_hub.logging.UVICORN_LOGGING_CONFIG)
    yield
    logging.shutdown()


def test_loggers(capsys, faker, apply_logging_config):
    fake_message = faker.sentence()

    logging.getLogger("cata_log_hub").error(fake_message)

    assert fake_message in capsys.readouterr().err
    assert fake_message in (get_settings().logs_path / "cata-log-hub.log").read_text()
    assert fake_message in (get_settings().logs_path / "root.log").read_text()

    fake_message = faker.sentence()

    logging.getLogger("sqlalchemy").error(fake_message)

    assert fake_message in capsys.readouterr().err
    assert fake_message in (get_settings().logs_path / "sqlalchemy.log").read_text()
    assert fake_message in (get_settings().logs_path / "root.log").read_text()

    fake_message = faker.sentence()

    logging.getLogger("alembic").error(fake_message)

    assert fake_message in capsys.readouterr().err
    assert fake_message in (get_settings().logs_path / "alembic.log").read_text()
    assert fake_message in (get_settings().logs_path / "root.log").read_text()

    fake_message = faker.sentence()

    logging.getLogger("apscheduler").error(fake_message)

    assert fake_message in capsys.readouterr().err
    assert fake_message in (get_settings().logs_path / "apscheduler.log").read_text()
    assert fake_message in (get_settings().logs_path / "root.log").read_text()

    fake_message = faker.sentence()

    logging.getLogger("other").error(fake_message)

    assert fake_message in capsys.readouterr().err
    assert fake_message in (get_settings().logs_path / "root.log").read_text()

    fake_message = faker.sentence()

    logging.getLogger("uvicorn").error(fake_message)

    assert fake_message in capsys.readouterr().err
    assert fake_message in (get_settings().logs_path / "uvicorn.log").read_text()
    assert fake_message in (get_settings().logs_path / "root.log").read_text()

    fake_message = faker.sentence()

    logging.getLogger("uvicorn.error").error(fake_message)

    assert fake_message in capsys.readouterr().err
    assert fake_message in (get_settings().logs_path / "uvicorn.log").read_text()
    assert fake_message in (get_settings().logs_path / "root.log").read_text()

    fake_message = faker.sentence()

    logging.getLogger("uvicorn.access").error(fake_message)

    assert fake_message not in capsys.readouterr().err
    assert fake_message in (get_settings().logs_path / "access.log").read_text()
    assert fake_message not in (get_settings().logs_path / "root.log").read_text()
