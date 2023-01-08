# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.util.countries import get_countries, get_country


class MockConfig:
    CUSTOM_COUNTRIES = {
        'XK': 'Kosovo',  # does not exist
        'TW': 'Taiwan, China',  # different name
    }


@pytest.mark.parametrize('country', list(MockConfig.CUSTOM_COUNTRIES))
def test_get_countries(mocker, country):
    mocker.patch('indico.util.countries.config', MockConfig())
    countries = get_countries()
    assert countries[country] == MockConfig.CUSTOM_COUNTRIES[country]


@pytest.mark.parametrize('country', list(MockConfig.CUSTOM_COUNTRIES))
def test_get_county(mocker, country):
    mocker.patch('indico.util.countries.config', MockConfig())
    assert get_country(country) == MockConfig.CUSTOM_COUNTRIES[country]
