# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

from xml.sax.saxutils import quoteattr, escape

class CurrencyRegistry:
    _items = ["","CHF","EUR","USD", "GBP", "CZK"]

    def getList( self ):
        return self._items
    getList=classmethod(getList)

    def getSelectItemsHTML( self, selCurrency="" ):
        l=[]
        for title in self._items:
            selected=""
            if title==selCurrency:
                selected=" selected"
            l.append("""<option value=%s%s>%s</option>"""%(quoteattr(title),
                                        selected, escape(title)))
        return "".join(l)
    getSelectItemsHTML=classmethod(getSelectItemsHTML)