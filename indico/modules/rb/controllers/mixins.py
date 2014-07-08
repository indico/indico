# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.


class AttributeSetterMixin:
    """Utility class to make retrieval of parameters from requests"""

    def setParam(self, attrName, params, paramName=None, default=None, callback=None):
        """ Sets the given attribute from params
            If there is no value to set, uses default
            Otherwise, auto strips and if callback given, pre-processes value and then sets
        """
        if not paramName:
            paramName = attrName
        val = params.get(paramName)
        if val and val.strip():
            val = val.strip()
            if callback:
                val = callback(val)
            setattr(self, attrName, val)
        else:
            setattr(self, attrName, default)
