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

import pytest

from cata_log.providers import plugins
from cata_log.providers.base import Provider
from cata_log.settings import get_settings

TEST_PLUGIN = """
from cata_log.providers.base import Provider

class TestPluginProvider(Provider):
    name = "test-plugin"
    uid= "test_plugin"

    def _get_page(self, page_number):
        pass
    def _get_catalog_data(self):
        pass
    def _get_valid_since(self):
        pass
    def _get_valid_until(self):
        pass
"""


@pytest.fixture
def test_plugin_path():
    test_plugin_path = get_settings().plugin_path / "test-plugin.py"
    test_plugin_path.write_text(TEST_PLUGIN)
    yield test_plugin_path
    test_plugin_path.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def unload_test_plugin():
    yield
    if "test_plugin" in Provider._registry:
        del Provider._registry["test_plugin"]


def test_load_plugins__no_plugins():
    assert "test_plugin" not in Provider.get_class_uids()

    plugins.load_plugins()

    assert "test_plugin" not in Provider.get_class_uids()


def test_load_plugins(test_plugin_path):
    assert "test_plugin" not in Provider.get_class_uids()

    plugins.load_plugins()

    assert "test_plugin" in Provider.get_class_uids()


def test_load_plugins__bad_plugin(test_plugin_path):
    test_plugin_path.write_text(TEST_PLUGIN.replace("pass", ""))

    assert "test_plugin" not in Provider.get_class_uids()

    plugins.load_plugins()

    assert "test_plugin" not in Provider.get_class_uids()


def test_load_plugins__raising_plugin__before(test_plugin_path):
    test_plugin_path.write_text("raise ValueError\n" + TEST_PLUGIN)

    assert "test_plugin" not in Provider.get_class_uids()

    plugins.load_plugins()

    assert "test_plugin" not in Provider.get_class_uids()


def test_load_plugins__raising_plugin__after(test_plugin_path):
    test_plugin_path.write_text(TEST_PLUGIN + "\nraise ValueError")

    assert "test_plugin" not in Provider.get_class_uids()

    plugins.load_plugins()

    assert "test_plugin" in Provider.get_class_uids()


def test_load_plugins__unloadable_plugin(test_plugin_path):
    test_plugin_path.unlink()
    test_plugin_path.mkdir()

    assert "test_plugin" not in Provider.get_class_uids()

    plugins.load_plugins()

    assert "test_plugin" not in Provider.get_class_uids()

    test_plugin_path.rmdir()


def test_load_plugins__subdir_plugin(test_plugin_path):
    subdir_path = test_plugin_path.parent / "subdir"
    subdir_path.mkdir()
    test_plugin_subdir_path = test_plugin_path.move_into(subdir_path)

    assert "test_plugin" not in Provider.get_class_uids()

    plugins.load_plugins()

    assert "test_plugin" in Provider.get_class_uids()

    test_plugin_subdir_path.unlink()
