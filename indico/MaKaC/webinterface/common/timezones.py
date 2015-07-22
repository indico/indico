# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

############################
# Fermi timezone awareness #
############################

from xml.sax.saxutils import quoteattr, escape
from indico.core.config import Config


class TimezoneRegistry:
    _items = Config.getInstance().getTimezoneList()

    @classmethod
    def getList( self ):
        return self._items

    @classmethod
    def getShortSelectItemsHTML(cls, selTitle=""):
        l=[]
        for title in cls._items:
            selected=""
            if title==selTitle:
                selected=" selected"
            screenTitle = title
            l.append("""<option value=%s%s>%s</option>"""%(quoteattr(title),
                                        selected, escape(screenTitle)))
        return "".join(l)

