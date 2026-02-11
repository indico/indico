# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
import warnings
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


def get_country(code, locale=None, *, use_fallback=False):
    if locale is None:
        locale = get_current_locale()
    return _get_country(code, locale) or (code if use_fallback else None)


@lru_cache
@make_interceptable
def _get_countries(locale):
    _countries = {country.alpha_2: getattr(country, 'common_name', country.name) for country in pycountry.countries}
    _countries = {code: locale.territories.get(code, name) for code, name in _countries.items()}
    _apply_custom_country(_countries, locale)

    return ImmutableDict(sorted(_countries.items(), key=lambda item: str_to_ascii(remove_accents(item[1]))))


def _apply_custom_country(countries, locale):
    for alpha_2, value in config.CUSTOM_COUNTRIES.items():
        if value is None:
            countries.pop(alpha_2, None)
        elif isinstance(value, str):
            countries[alpha_2] = value
        elif isinstance(value, dict):
            locale_str = str(locale)
            if locale_str in value:
                countries[alpha_2] = value[locale_str]
            elif (lang := locale_str.split('_', maxsplit=1)[0]) in value:  # If not full locale, try just language
                countries[alpha_2] = value[lang]
            else:
                warnings.warn(
                    f'Locale {locale_str!r} not found for country {alpha_2!r} in CUSTOM_COUNTRIES, falling back to '
                    'ISO 3166 name.',
                    stacklevel=1
                )


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
