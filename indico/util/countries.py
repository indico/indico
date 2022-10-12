# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pycountry
from werkzeug.datastructures import ImmutableDict

from indico.core.config import config
from indico.util.caching import memoize
from indico.util.i18n import get_current_locale


def get_countries(locale=None):
    if locale is None:
        locale = get_current_locale()
    return _get_countries(locale)


@memoize
def _get_countries(locale):
    _countries = {country.alpha_2: getattr(country, 'common_name', country.name) for country in pycountry.countries}
    _countries = {code: locale.territories.get(code, name) for code, name in _countries.items()}
    _countries.update(config.CUSTOM_COUNTRIES)
    return ImmutableDict(_countries)


def get_country(code, locale=None):
    if locale is None:
        locale = get_current_locale()
    return _get_country(code, locale)


def get_country_reverse(name, locale=None):
    """Get the country code from a country name.

    Note: You almost certainly should not use this but rather store
    the country code and use it directly.
    The only reason this util exists is that the friendly_data handling
    for registration form fields is one big mess (human-friendly vs
    machine-friendly)...
    """
    if locale is None:
        locale = get_current_locale()
    return next((code for code, title in get_countries(locale).items() if title == name), None)


@memoize
def _get_country(code, locale):
    try:
        return _get_countries(locale)[code]
    except KeyError:
        country = pycountry.historic_countries.get(alpha_2=code)
        return country.name if country else None
