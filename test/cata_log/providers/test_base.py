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
from celery.schedules import crontab

from cata_log import exceptions
from cata_log.providers import Provider
from cata_log.providers.regions import Region
from cata_log.utils.page_numbers import PageNumber
from test.cata_log.conftest import SideEffects


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
    assert isinstance(provider_class.schedule, crontab)
    assert isinstance(provider_class.first_page_number, int)
    assert isinstance(provider_class.configuration, tuple)
    for config in provider_class.configuration:
        if config.default:
            config.parse_as(config.default)


@pytest.mark.parametrize(
    ("side_effect", "expected_error"),
    [
        (SideEffects.DONOTHING, None),
        (SideEffects.HTTP_400, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_500, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_404, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.TRANSPORTERROR, exceptions.NetworkError),
        (SideEffects.KEYERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.EXCEPTION, exceptions.ProviderBrokenWarning),
        (SideEffects.CATALOGUNAVAILABLE, exceptions.CatalogUnavailableWarning),
    ],
)
def test_get_catalog_data(provider_test_class, side_effect, expected_error):
    if expected_error:
        with pytest.raises(expected_error):
            provider_test_class(
                {"side_effect": side_effect, **provider_test_class.default_config}
            )
    else:
        provider_test_class(
            {"side_effect": side_effect, **provider_test_class.default_config}
        )


@pytest.mark.parametrize(
    ("side_effect", "expected_error"),
    [
        (SideEffects.DONOTHING, None),
        (SideEffects.HTTP_400, exceptions.ProviderBrokenWarning),
        (SideEffects.HTTP_500, exceptions.ProviderBrokenWarning),
        (SideEffects.HTTP_404, exceptions.ProviderBrokenWarning),
        (SideEffects.TRANSPORTERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.KEYERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.EXCEPTION, exceptions.ProviderBrokenWarning),
        (SideEffects.CATALOGUNAVAILABLE, exceptions.ProviderBrokenWarning),
    ],
)
def test_get_valid_since(provider_test_class, side_effect, expected_error):
    if expected_error:
        with pytest.raises(expected_error):
            provider_test_class(
                {
                    "side_effect": side_effect,
                    "pass_get_catalog_data": "True",
                    **provider_test_class.default_config,
                }
            ).get_valid_until()
    else:
        result = provider_test_class(
            {
                "side_effect": side_effect,
                "pass_get_catalog_data": "True",
                **provider_test_class.default_config,
            }
        ).get_valid_until()

        assert result


@pytest.mark.parametrize(
    ("side_effect", "expected_error"),
    [
        (SideEffects.DONOTHING, None),
        (SideEffects.HTTP_400, exceptions.ProviderBrokenWarning),
        (SideEffects.HTTP_500, exceptions.ProviderBrokenWarning),
        (SideEffects.HTTP_404, exceptions.ProviderBrokenWarning),
        (SideEffects.TRANSPORTERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.KEYERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.EXCEPTION, exceptions.ProviderBrokenWarning),
        (SideEffects.CATALOGUNAVAILABLE, exceptions.ProviderBrokenWarning),
    ],
)
def test_get_valid_until(provider_test_class, side_effect, expected_error):
    if expected_error:
        with pytest.raises(expected_error):
            provider_test_class(
                {
                    "side_effect": side_effect,
                    "pass_get_catalog_data": "True",
                    **provider_test_class.default_config,
                }
            ).get_valid_until()
    else:
        result = provider_test_class(
            {
                "side_effect": side_effect,
                "pass_get_catalog_data": "True",
                **provider_test_class.default_config,
            }
        ).get_valid_until()

        assert result


@pytest.mark.parametrize(
    ("side_effect", "page_number", "expected_error"),
    [
        (SideEffects.DONOTHING, 0, None),
        (SideEffects.DONOTHING, 6, None),
        (SideEffects.HTTP_400, 0, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_400, 3, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_500, 0, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_500, 4, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_404, 0, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_404, 6, exceptions.PagesExhausted),
        (SideEffects.TRANSPORTERROR, 0, exceptions.NetworkError),
        (SideEffects.TRANSPORTERROR, 24, exceptions.NetworkError),
        (SideEffects.KEYERROR, 0, exceptions.ProviderBrokenWarning),
        (SideEffects.KEYERROR, 10, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, 0, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, 94, exceptions.ProviderBrokenWarning),
        (SideEffects.EXCEPTION, 0, exceptions.ProviderBrokenWarning),
        (SideEffects.EXCEPTION, 5, exceptions.ProviderBrokenWarning),
        (
            SideEffects.PAGESEXHAUSTED,
            0,
            exceptions.ProviderMisconfiguredOrBrokenWarning,
        ),
        (SideEffects.PAGESEXHAUSTED, 34, exceptions.PagesExhausted),
        (SideEffects.CATALOGUNAVAILABLE, 0, exceptions.CatalogUnavailableWarning),
        (
            SideEffects.CATALOGUNAVAILABLE,
            6,
            exceptions.ProviderMisconfiguredOrBrokenWarning,
        ),
    ],
)
def test_get_page(
    provider_test_class,
    side_effect,
    page_number,
    expected_error,
):
    if expected_error:
        with pytest.raises(expected_error):
            provider_test_class(
                {
                    "side_effect": side_effect,
                    "pass_get_catalog_data": "True",
                    **provider_test_class.default_config,
                }
            ).get_page(
                PageNumber(
                    page_number, start_number=provider_test_class.first_page_number
                )
            )
    else:
        result = provider_test_class(
            {
                "side_effect": side_effect,
                "pass_get_catalog_data": "True",
                **provider_test_class.default_config,
            }
        ).get_page(
            PageNumber(page_number, start_number=provider_test_class.first_page_number)
        )

        assert result


@pytest.mark.parametrize(
    ("side_effect", "expected_error"),
    [
        (SideEffects.DONOTHING, None),
        (SideEffects.HTTP_400, exceptions.CatalogUnavailableWarning),
        (SideEffects.HTTP_500, exceptions.CatalogUnavailableWarning),
        (SideEffects.HTTP_404, exceptions.CatalogUnavailableWarning),
        (SideEffects.TRANSPORTERROR, exceptions.NetworkError),
        (SideEffects.KEYERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.EXCEPTION, exceptions.ProviderBrokenWarning),
        (SideEffects.CATALOGUNAVAILABLE, exceptions.CatalogUnavailableWarning),
    ],
)
def test_get_catalog_data__preview(
    preview_provider_test_class,
    side_effect,
    expected_error,
):
    if expected_error:
        with pytest.raises(expected_error):
            preview_provider_test_class(
                {
                    "side_effect": side_effect,
                    **preview_provider_test_class.default_config,
                }
            )
    else:
        preview_provider_test_class(
            {"side_effect": side_effect, **preview_provider_test_class.default_config}
        )


@pytest.mark.parametrize(
    ("side_effect", "expected_error"),
    [
        (SideEffects.DONOTHING, None),
        (SideEffects.HTTP_400, exceptions.ProviderBrokenWarning),
        (SideEffects.HTTP_500, exceptions.ProviderBrokenWarning),
        (SideEffects.HTTP_404, exceptions.ProviderBrokenWarning),
        (SideEffects.TRANSPORTERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.KEYERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.EXCEPTION, exceptions.ProviderBrokenWarning),
        (SideEffects.CATALOGUNAVAILABLE, exceptions.ProviderBrokenWarning),
    ],
)
def test_get_valid_since__preview(
    preview_provider_test_class,
    side_effect,
    expected_error,
):
    if expected_error:
        with pytest.raises(expected_error):
            preview_provider_test_class(
                {
                    "side_effect": side_effect,
                    "pass_get_catalog_data": "True",
                    **preview_provider_test_class.default_config,
                }
            ).get_valid_until()
    else:
        result = preview_provider_test_class(
            {
                "side_effect": side_effect,
                "pass_get_catalog_data": "True",
                **preview_provider_test_class.default_config,
            }
        ).get_valid_until()

        assert result


@pytest.mark.parametrize(
    ("side_effect", "expected_error"),
    [
        (SideEffects.DONOTHING, None),
        (SideEffects.HTTP_400, exceptions.ProviderBrokenWarning),
        (SideEffects.HTTP_500, exceptions.ProviderBrokenWarning),
        (SideEffects.HTTP_404, exceptions.ProviderBrokenWarning),
        (SideEffects.TRANSPORTERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.KEYERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, exceptions.ProviderBrokenWarning),
        (SideEffects.EXCEPTION, exceptions.ProviderBrokenWarning),
        (SideEffects.CATALOGUNAVAILABLE, exceptions.ProviderBrokenWarning),
    ],
)
def test_get_valid_until__preview(
    preview_provider_test_class,
    side_effect,
    expected_error,
):
    if expected_error:
        with pytest.raises(expected_error):
            preview_provider_test_class(
                {
                    "side_effect": side_effect,
                    "pass_get_catalog_data": "True",
                    **preview_provider_test_class.default_config,
                }
            ).get_valid_until()
    else:
        result = preview_provider_test_class(
            {
                "side_effect": side_effect,
                "pass_get_catalog_data": "True",
                **preview_provider_test_class.default_config,
            }
        ).get_valid_until()

        assert result


@pytest.mark.parametrize(
    ("side_effect", "page_number", "expected_error"),
    [
        (SideEffects.DONOTHING, 0, None),
        (SideEffects.DONOTHING, 6, None),
        (SideEffects.HTTP_400, 0, exceptions.CatalogUnavailableWarning),
        (SideEffects.HTTP_400, 3, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_500, 0, exceptions.CatalogUnavailableWarning),
        (SideEffects.HTTP_500, 4, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_404, 0, exceptions.CatalogUnavailableWarning),
        (SideEffects.HTTP_404, 6, exceptions.PagesExhausted),
        (SideEffects.TRANSPORTERROR, 0, exceptions.NetworkError),
        (SideEffects.TRANSPORTERROR, 24, exceptions.NetworkError),
        (SideEffects.KEYERROR, 0, exceptions.ProviderBrokenWarning),
        (SideEffects.KEYERROR, 10, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, 0, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, 94, exceptions.ProviderBrokenWarning),
        (SideEffects.EXCEPTION, 0, exceptions.ProviderBrokenWarning),
        (SideEffects.EXCEPTION, 5, exceptions.ProviderBrokenWarning),
        (
            SideEffects.PAGESEXHAUSTED,
            0,
            exceptions.ProviderMisconfiguredOrBrokenWarning,
        ),
        (SideEffects.PAGESEXHAUSTED, 34, exceptions.PagesExhausted),
        (SideEffects.CATALOGUNAVAILABLE, 0, exceptions.CatalogUnavailableWarning),
        (
            SideEffects.CATALOGUNAVAILABLE,
            6,
            exceptions.ProviderMisconfiguredOrBrokenWarning,
        ),
    ],
)
def test_get_page__preview(
    preview_provider_test_class,
    side_effect,
    page_number,
    expected_error,
):
    if expected_error:
        with pytest.raises(expected_error):
            preview_provider_test_class(
                {
                    "side_effect": side_effect,
                    "pass_get_catalog_data": "True",
                    **preview_provider_test_class.default_config,
                }
            ).get_page(
                PageNumber(
                    page_number,
                    start_number=preview_provider_test_class.first_page_number,
                )
            )
    else:
        result = preview_provider_test_class(
            {
                "side_effect": side_effect,
                "pass_get_catalog_data": "True",
                **preview_provider_test_class.default_config,
            }
        ).get_page(
            PageNumber(
                page_number, start_number=preview_provider_test_class.first_page_number
            )
        )

        assert result


@pytest.mark.parametrize(
    "config",
    [
        {
            "required_config": "asdf",
            "optional_config": "test",
            "typed_config": "4",
            "optional_typed_config": "2.31",
        },
        {
            "required_config": "",
            "optional_config": "test",
            "typed_config": "0",
            "optional_typed_config": "2.31",
        },
        {"required_config": "asdf", "typed_config": "4"},
        {
            "required_config": "asdf",
            "optional_config": "test",
            "typed_config": "4",
            "optional_typed_config": "2.31",
            "extra_config": "rgn",
        },
    ],
)
def test_validate_config__success(provider_test_class, config):
    validated_config = provider_test_class.validate_config(config)

    for configuration in provider_test_class.configuration:
        assert configuration.name in validated_config
        assert validated_config[configuration.name] == config.get(
            configuration.name, configuration.default
        )


@pytest.mark.parametrize(
    ("config", "missing_configs"),
    [
        (
            {
                "required_config": "asdf",
                "optional_config": "test",
                "optional_typed_config": "2.31",
            },
            ["typed_config"],
        ),
        (
            {
                "optional_config": "test",
                "typed_config": "4",
                "optional_typed_config": "2.31",
            },
            ["required_config"],
        ),
        (
            {"optional_config": "test", "optional_typed_config": "2.31"},
            ["required_config", "typed_config"],
        ),
        ({"optional_typed_config": "2.31"}, ["required_config", "typed_config"]),
        ({}, ["required_config", "typed_config"]),
    ],
)
def test_validate_config__missing_field(provider_test_class, config, missing_configs):
    with pytest.raises(exceptions.ProviderIncompleteConfigWarning) as error:  # noqa: PT012  # needed to check missing_configs
        provider_test_class.validate_config(config)

        for missing_config in missing_configs:
            assert missing_config in error.missing_configs


@pytest.mark.parametrize(
    ("config", "bad_configs"),
    [
        (
            {
                "required_config": "asdf",
                "typed_config": "notanumber",
            },
            ["typed_config"],
        ),
        (
            {
                "required_config": "asdf",
                "typed_config": "4",
                "optional_typed_config": "badfloat",
            },
            ["optional_typed_config"],
        ),
        (
            {
                "required_config": "asdf",
                "typed_config": "string",
                "optional_typed_config": "badint",
            },
            ["typed_config", "optional_typed_config"],
        ),
    ],
)
def test_validate_config__invalid_field(provider_test_class, config, bad_configs):
    with pytest.raises(exceptions.ProviderInvalidConfigWarning) as error:  # noqa: PT012  # needed to check bad_configs
        provider_test_class.validate_config(config)

        for bad_config in bad_configs:
            assert bad_config in error.bad_configs
