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

############################
# Fermi timezone awareness #
############################

from datetime import datetime
from pytz import timezone
from xml.sax.saxutils import quoteattr, escape
from indico.core.config import Config
from MaKaC.i18n import _


def convertTime(d,tz):
    if str(d.tzinfo) == 'None':
       return_d = datetime(d.year,d.month,d.day,d.hour,d.minute,tzinfo=timezone('UTC'))
    else:
       return_d = d.astimezone(timezone(tz))
    return (return_d)

class TimezoneRegistry:
    _items = Config.getInstance().getTimezoneList()

    @classmethod
    def getList( self ):
        return self._items

    def getShortSelectItemsHTML( self, selTitle="", localTZ="" ):
        l=[]
        for title in self._items:
            selected=""
            if title==selTitle:
                selected=" selected"
            screenTitle = title
            l.append("""<option value=%s%s>%s</option>"""%(quoteattr(title),
                                        selected, escape(screenTitle)))
        return "".join(l)
    getShortSelectItemsHTML=classmethod(getShortSelectItemsHTML)


class DisplayTimezoneRegistry:
    _items = ['MyTimezone','Event Timezone']

    def getList( self ):
        return self._items

    getList=classmethod(getList)

    def getSelectItemsHTML( self, selTitle="" ):
        l=[]
        for title in self._items:
            selected=""
            if title==selTitle:
                selected=" selected"
            l.append("""<option value=%s%s>%s</option>"""%(quoteattr(title),
                                        selected, escape(title)))
        return "".join(l)
    getSelectItemsHTML=classmethod(getSelectItemsHTML)
