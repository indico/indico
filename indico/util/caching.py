# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


# http://code.activestate.com/recipes/576563-cached-property/
# Modified to use a volatile dict so it doesn't go to the DB under any circumstances
def cached_property(f):
    """returns a cached property that is calculated by function f"""
    def get(self):
        try:
            return self._v_property_cache[f]
        except AttributeError:
            self._v_property_cache = {}
            x = self._v_property_cache[f] = f(self)
            return x
        except KeyError:
            x = self._v_property_cache[f] = f(self)
            return x
    return property(get)
