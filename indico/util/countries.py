# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import pycountry
from werkzeug.datastructures import ImmutableDict

from indico.core.config import config
from indico.util.caching import memoize


@memoize
def get_countries():
    _countries = {country.alpha_2: getattr(country, 'common_name', country.name) for country in pycountry.countries}
    _countries.update(config.CUSTOM_COUNTRIES)
    return ImmutableDict(_countries)


@memoize
def get_country(code):
    try:
        return get_countries()[code]
    except KeyError:
        country = pycountry.historic_countries.get(alpha_2=code)
        return country.name if country else None
