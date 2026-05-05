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
from apscheduler.triggers.cron import CronTrigger

from cata_log.providers import Provider
from cata_log.providers.configuration import Configuration
from cata_log.providers.regions import Region


@pytest.mark.parametrize("provider_class", Provider._registry.values())
def test_registered_classes__attributes(provider_class):
    assert issubclass(provider_class, Provider)
    assert provider_class.name
    assert isinstance(provider_class.name, str)
    assert provider_class.description
    assert isinstance(provider_class.description, str)
    assert provider_class.url
    assert isinstance(provider_class.url, str)
    assert provider_class.page_file_extension
    assert isinstance(provider_class.page_file_extension, str)
    assert provider_class.region
    assert issubclass(provider_class.region, Region)
    assert provider_class.schedule
    assert isinstance(provider_class.schedule, str)
    assert CronTrigger.from_crontab(provider_class.schedule)
    assert isinstance(provider_class.jitter, int)
    assert provider_class.jitter < 86400
    assert isinstance(provider_class.first_page_number, int)
    assert isinstance(provider_class.configuration, tuple)
    for config in provider_class.configuration:
        assert isinstance(config, Configuration)
    for config in provider_class.configuration:
        if config.default:
            config.parse_as(config.default)
    assert provider_class.uid
    assert provider_class.uid in Provider._registry
