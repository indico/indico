# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.util.countries import _get_countries, _get_country, get_countries, get_country


class MockConfig:
    CUSTOM_COUNTRIES = {
        'XK': 'Kosovo',  # does not exist
        'TW': 'Taiwan, China',  # different name
    }


class MockConfigDeleteCountry:
    CUSTOM_COUNTRIES = {
        **MockConfig.CUSTOM_COUNTRIES,
        'AQ': None  # remove country
    }


@pytest.fixture(autouse=True)
def _clear_country_cache():
    # those utils are memoized and other test code may call them before/after the tests
    # in here and we need to use our custom mocked data instead of old cached data
    _get_country.cache_clear()
    _get_countries.cache_clear()
    yield
    _get_country.cache_clear()
    _get_countries.cache_clear()


@pytest.mark.parametrize('country', list(MockConfig.CUSTOM_COUNTRIES))
def test_get_countries(mocker, country):
    mocker.patch('indico.util.countries.config', MockConfig())
    countries = get_countries()
    assert countries[country] == MockConfig.CUSTOM_COUNTRIES[country]


@pytest.mark.parametrize('country', list(MockConfig.CUSTOM_COUNTRIES))
def test_get_country(mocker, country):
    mocker.patch('indico.util.countries.config', MockConfig())
    assert get_country(country) == MockConfig.CUSTOM_COUNTRIES[country]


def test_get_countries_deleted(mocker):
    mocker.patch('indico.util.countries.config', MockConfigDeleteCountry())
    countries = get_countries()
    assert 'AQ' not in countries


def test_get_country_deleted(mocker):
    mocker.patch('indico.util.countries.config', MockConfigDeleteCountry())
    assert get_country('AQ') is None
    assert get_country('AQ', use_fallback=True) == 'AQ'
