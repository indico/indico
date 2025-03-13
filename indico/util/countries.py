# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
from functools import lru_cache

import pycountry
from werkzeug.datastructures import ImmutableDict

from indico.core.config import config
from indico.util.i18n import get_current_locale
from indico.util.signals import make_interceptable
from indico.util.string import remove_accents, str_to_ascii


def get_countries(locale=None):
    if locale is None:
        locale = get_current_locale()
    return _get_countries(locale)


@lru_cache
@make_interceptable
def _get_countries(locale):
    _countries = {country.alpha_2: getattr(country, 'common_name', country.name) for country in pycountry.countries}
    _countries = {code: locale.territories.get(code, name) for code, name in _countries.items()}
    _countries.update(config.CUSTOM_COUNTRIES)
    return ImmutableDict(sorted(_countries.items(), key=lambda item: str_to_ascii(remove_accents(item[1]))))


def get_country(code, locale=None):
    if locale is None:
        locale = get_current_locale()
    return _get_country(code, locale)


def get_country_reverse(name, locale=None, case_sensitive=True):
    """Get the country code from a country name.

    Note: You almost certainly should not use this but rather store
    the country code and use it directly.
    The only reason this util exists is that the friendly_data handling
    for registration form fields is one big mess (human-friendly vs
    machine-friendly)...
    """
    if locale is None:
        locale = get_current_locale()
    return next((code for code, title in get_countries(locale).items()
                 if title == name or (not case_sensitive and title.lower() == name.lower())), None)


def get_countries_regex(locale=None):
    """Get a regex to search for country names in a string."""
    if locale is None:
        locale = get_current_locale()
    return _get_countries_regex(locale)


@lru_cache
def _get_countries_regex(locale):
    return re.compile('|'.join(fr'\b{re.escape(title)}\b' for title in get_countries(locale).values()), re.IGNORECASE)


@lru_cache
def _get_country(code, locale):
    try:
        return _get_countries(locale)[code]
    except KeyError:
        country = pycountry.historic_countries.get(alpha_2=code)
        return country.name if country else None
