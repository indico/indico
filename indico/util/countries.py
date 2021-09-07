# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
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
    _countries.update(config.CUSTOM_COUNTRIES)
    _countries = {code: locale.territories.get(code, name) for code, name in _countries.items()}
    return ImmutableDict(_countries)


def get_country(code, locale=None):
    if locale is None:
        locale = get_current_locale()
    return _get_country(code, locale)


@memoize
def _get_country(code, locale):
    try:
        return _get_countries(locale)[code]
    except KeyError:
        country = pycountry.historic_countries.get(alpha_2=code)
        return country.name if country else None
