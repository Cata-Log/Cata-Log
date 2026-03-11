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

from types import MappingProxyType

from celery.schedules import crontab

from cata_log.providers import catalog_registry
from cata_log.providers.base import BaseProvider
from cata_log.providers.regions import Region


def test_registered_classes():
    for catalog_class in catalog_registry.values():
        assert issubclass(catalog_class, BaseProvider)
        assert catalog_class.name
        assert isinstance(catalog_class.name, str)
        assert catalog_class.description
        assert isinstance(catalog_class.description, str)
        assert catalog_class.region
        assert issubclass(catalog_class.region, Region)
        assert catalog_class.schedule
        assert isinstance(catalog_class.schedule, crontab)
        assert isinstance(catalog_class.first_page_number, int)
        assert isinstance(catalog_class.configuration, MappingProxyType)
