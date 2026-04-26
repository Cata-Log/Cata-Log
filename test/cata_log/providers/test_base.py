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

from cata_log import exceptions
from cata_log.providers import Provider
from cata_log.utils.page_numbers import PageNumber
from test.cata_log.conftest import SideEffects


def test_duplicate_provider(provider_test_class):
    with pytest.raises(exceptions.ProviderRegistrationWarning):

        class DuplicateProvider(Provider):
            uid = provider_test_class.uid


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
                {
                    "side_effect": side_effect,
                    **provider_test_class.default_configuration,
                }
            )
    else:
        provider_test_class(
            {"side_effect": side_effect, **provider_test_class.default_configuration}
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
                    **provider_test_class.default_configuration,
                }
            ).get_valid_until()
    else:
        result = provider_test_class(
            {
                "side_effect": side_effect,
                "pass_get_catalog_data": "True",
                **provider_test_class.default_configuration,
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
                    **provider_test_class.default_configuration,
                }
            ).get_valid_until()
    else:
        result = provider_test_class(
            {
                "side_effect": side_effect,
                "pass_get_catalog_data": "True",
                **provider_test_class.default_configuration,
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
        (SideEffects.TRANSPORTERROR, 2, exceptions.NetworkError),
        (SideEffects.KEYERROR, 0, exceptions.ProviderBrokenWarning),
        (SideEffects.KEYERROR, 1, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, 0, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, 9, exceptions.ProviderBrokenWarning),
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
                    **provider_test_class.default_configuration,
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
                **provider_test_class.default_configuration,
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
                    **preview_provider_test_class.default_configuration,
                }
            )
    else:
        preview_provider_test_class(
            {
                "side_effect": side_effect,
                **preview_provider_test_class.default_configuration,
            }
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
                    **preview_provider_test_class.default_configuration,
                }
            ).get_valid_until()
    else:
        result = preview_provider_test_class(
            {
                "side_effect": side_effect,
                "pass_get_catalog_data": "True",
                **preview_provider_test_class.default_configuration,
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
                    **preview_provider_test_class.default_configuration,
                }
            ).get_valid_until()
    else:
        result = preview_provider_test_class(
            {
                "side_effect": side_effect,
                "pass_get_catalog_data": "True",
                **preview_provider_test_class.default_configuration,
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
        (SideEffects.TRANSPORTERROR, 2, exceptions.NetworkError),
        (SideEffects.KEYERROR, 0, exceptions.ProviderBrokenWarning),
        (SideEffects.KEYERROR, 1, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, 0, exceptions.ProviderBrokenWarning),
        (SideEffects.VALUEERROR, 9, exceptions.ProviderBrokenWarning),
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
                    **preview_provider_test_class.default_configuration,
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
                **preview_provider_test_class.default_configuration,
            }
        ).get_page(
            PageNumber(
                page_number, start_number=preview_provider_test_class.first_page_number
            )
        )

        assert result


@pytest.mark.parametrize(
    "configuration",
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
def test_validate_configuration__success(provider_test_class, configuration):
    validated_configuration = provider_test_class.validate_configuration(configuration)

    for config in provider_test_class.configuration:
        assert config.name in validated_configuration
        assert validated_configuration[config.name] == configuration.get(
            config.name, config.default
        )


@pytest.mark.parametrize(
    ("configuration", "missing_configurations"),
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
def test_validate_configuration__missing_field(
    provider_test_class, configuration, missing_configurations
):
    with pytest.raises(exceptions.ProviderIncompleteConfigurationWarning) as exc_info:
        provider_test_class.validate_configuration(configuration)

    for missing_config in missing_configurations:
        assert missing_config in exc_info.value.bad_configurations


@pytest.mark.parametrize(
    ("configuration", "bad_configurations"),
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
def test_validate_configuration__invalid_field(
    provider_test_class, configuration, bad_configurations
):
    with pytest.raises(exceptions.ProviderInvalidConfigurationWarning) as exc_info:
        provider_test_class.validate_configuration(configuration)

    for bad_config in bad_configurations:
        assert bad_config in exc_info.value.bad_configurations
