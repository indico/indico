# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import pycountry
from indico.core.config import Config


class CountryHolder(object):
    """
    Contains all countries in the world
    """

    _countries = dict((country.alpha2.encode('utf-8'), country.name.encode('utf-8'))
                      for country in pycountry.countries)
    _countries.update(Config.getInstance().getCustomCountries())

    @classmethod
    def getCountries(cls):
        """
        Return the whole country dictionary
        """
        return cls._countries

    @classmethod
    def getCountryList(cls):
        """
        Returns all country names
        """
        return cls._countries.values()

    @classmethod
    def getCountryById(cls, cid):
        """
        Returns the country, given its ID
        """
        country_name = cls._countries.get(cid, None)
        if country_name:
            return country_name
        else:
            try:
                return pycountry.historic_countries.get(alpha2=cid).name.encode('utf-8')
            except KeyError:
                return None

    @classmethod
    def getCountryKeys(cls):
        """
        Returns all country ids
        """
        return cls._countries.keys()

    @classmethod
    def getCountrySortedKeys(cls):
        """
        Country ids, sorted alphabetically by country name
        """
        keys = cls.getCountryKeys()
        keys.sort(cls._sortByValue)
        return keys

    @classmethod
    def _sortByValue(cls, v1, v2):
        """
        Auxiliary function for country id sorting
        """
        return cmp(cls._countries[v1], cls._countries[v2])
