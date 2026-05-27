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

import httpx
import pytest
from freezegun import freeze_time
from pydantic import ValidationError

from cata_log import exceptions
from cata_log.providers import Provider
from cata_log.settings import get_settings
from cata_log.utils.page_numbers import PageNumber
from test.cata_log.conftest import SideEffects


def test_duplicate_provider(provider_test_class):
    class DuplicateProvider(Provider):
        uid = provider_test_class.uid

    assert provider_test_class.uid in Provider._registry
    assert Provider._registry[provider_test_class.uid] == provider_test_class


def test_relevant_datetime(faker, provider_test_class):
    with freeze_time(faker.date_time(tzinfo=UTC)):
        assert provider_test_class(
            provider_test_class.default_configuration,
        )._relevant_datetime == datetime.now(UTC)


def test_client(provider_test_class, fake_request):
    provider_class_client = provider_test_class(
        provider_test_class.default_configuration,
    )._client

    assert provider_class_client.follow_redirects is True
    assert provider_class_client.timeout.connect == get_settings().request_timeout
    assert "httpx" not in provider_class_client.headers["User-Agent"]

    assert provider_class_client.event_hooks["response"]
    with pytest.raises(
        httpx.HTTPStatusError,
        check=lambda status_error: status_error.response.status_code == 401,
    ):
        assert provider_class_client.event_hooks["response"][0](
            httpx.Response(status_code=401, request=fake_request)
        )
    with pytest.raises(
        httpx.HTTPStatusError,
        check=lambda status_error: status_error.response.status_code == 404,
    ):
        assert provider_class_client.event_hooks["response"][0](
            httpx.Response(status_code=404, request=fake_request)
        )
    with pytest.raises(
        httpx.HTTPStatusError,
        check=lambda status_error: status_error.response.status_code == 500,
    ):
        assert provider_class_client.event_hooks["response"][0](
            httpx.Response(status_code=500, request=fake_request)
        )
    provider_class_client.event_hooks["response"][0](
        httpx.Response(status_code=301, request=fake_request)
    )
    provider_class_client.event_hooks["response"][0](
        httpx.Response(status_code=200, request=fake_request)
    )


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
        assert result.tzinfo
        assert result == provider_test_class.const_valid_since.replace(
            tzinfo=provider_test_class.region.timezone
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
        assert result.tzinfo


@pytest.mark.parametrize(
    ("side_effect", "page_number", "expected_error"),
    [
        (SideEffects.DONOTHING, 0, None),
        (SideEffects.DONOTHING, 6, None),
        (SideEffects.HTTP_400, 0, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_400, 3, exceptions.PagesExhausted),
        (SideEffects.HTTP_500, 0, exceptions.ProviderMisconfiguredOrBrokenWarning),
        (SideEffects.HTTP_500, 4, exceptions.PagesExhausted),
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
            ).get_valid_since()
    else:
        result = preview_provider_test_class(
            {
                "side_effect": side_effect,
                "pass_get_catalog_data": "True",
                **preview_provider_test_class.default_configuration,
            }
        ).get_valid_since()

        assert result
        assert result.tzinfo
        assert result == preview_provider_test_class.const_valid_since.replace(
            tzinfo=preview_provider_test_class.region.timezone
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
        assert result.tzinfo


@pytest.mark.parametrize(
    ("side_effect", "page_number", "expected_error"),
    [
        (SideEffects.DONOTHING, 0, None),
        (SideEffects.DONOTHING, 6, None),
        (SideEffects.HTTP_400, 0, exceptions.CatalogUnavailableWarning),
        (SideEffects.HTTP_400, 3, exceptions.PagesExhausted),
        (SideEffects.HTTP_500, 0, exceptions.CatalogUnavailableWarning),
        (SideEffects.HTTP_500, 4, exceptions.PagesExhausted),
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


def test_relevant_datetime_preview(faker, preview_provider_test_class):
    with freeze_time(faker.date_time(tzinfo=UTC)):
        assert preview_provider_test_class(
            preview_provider_test_class.default_configuration,
        )._relevant_datetime == datetime.now(UTC) + timedelta(days=3)


def test_relevant_datetime_preview_error(faker, preview_provider_test_class):
    def bad__get_preview_timedelta(*args):
        raise ValueError

    preview_provider_test_class._get_preview_timedelta = bad__get_preview_timedelta
    with pytest.raises(exceptions.ProviderBrokenWarning):
        preview_provider_test_class(preview_provider_test_class.default_configuration)


@pytest.mark.parametrize(
    "configuration",
    [
        {
            "required_config": "asdf",
            "optional_config": "test",
            "typed_config": 4,
            "optional_typed_config": 2.31,
        },
        {
            "required_config": "",
            "optional_config": "test",
            "typed_config": 0,
            "optional_typed_config": 2.31,
        },
        {"required_config": "asdf", "typed_config": 4},
        {
            "required_config": "asdf",
            "optional_config": "test",
            "typed_config": 4,
            "optional_typed_config": 2.31,
            "extra_config": "rgn",
        },
    ],
)
def test_validate_configuration__success(provider_test_class, configuration):
    validated_configuration = provider_test_class.validate_configuration(
        configuration
    ).model_dump()

    for (
        config_name,
        config_field,
    ) in provider_test_class.Configuration.model_fields.items():
        assert config_name in validated_configuration
        assert validated_configuration[config_name] == configuration.get(
            config_name, config_field.default
        )


@pytest.mark.parametrize(
    ("configuration", "missing_configurations"),
    [
        (
            {
                "required_config": "asdf",
                "optional_config": "test",
                "optional_typed_config": 2.31,
            },
            ["typed_config"],
        ),
        (
            {
                "optional_config": "test",
                "typed_config": 4,
                "optional_typed_config": 2.31,
            },
            ["required_config"],
        ),
        (
            {"optional_config": "test", "optional_typed_config": 2.31},
            ["required_config", "typed_config"],
        ),
        ({"optional_typed_config": 2.31}, ["required_config", "typed_config"]),
        ({}, ["required_config", "typed_config"]),
    ],
)
def test_validate_configuration__missing_field(
    provider_test_class, configuration, missing_configurations
):
    with pytest.raises(exceptions.ProviderInvalidConfigurationWarning) as exc_info:
        provider_test_class.validate_configuration(configuration)
    assert exc_info.value.__cause__
    assert isinstance(exc_info.value.__cause__, ValidationError)


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
                "typed_config": 4,
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
    assert exc_info.value.__cause__
    assert isinstance(exc_info.value.__cause__, ValidationError)
