# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

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
        try:
            return pycountry.historic_countries.get(alpha_2=code).name
        except KeyError:
            return None
