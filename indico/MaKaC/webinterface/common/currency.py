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

from xml.sax.saxutils import quoteattr, escape
from MaKaC.plugins import PluginsHolder
from MaKaC.services.interface.rpc.common import ServiceError

class CurrencyRegistry:

    @classmethod
    def getList( self ):

        ph = PluginsHolder()
        if ph.hasPluginType("EPayment"):
            self._targetOption = ph.getPluginType("EPayment").getOption("customCurrency")
            currencies = self._targetOption.getValue()
            currenciesList = []
            for currency in currencies:
                currenciesList.append(currency["abbreviation"])
            return currenciesList

        else:
            raise ServiceError('ERR-PLUG3', 'pluginType: ' + str("EPayment") + ' does not exist, is not visible or not active')

        return [""]

    @classmethod
    def getSelectItemsHTML( self, selCurrency="" ):
        l=[]
        for title in self.getList():
            selected=""
            if title==selCurrency:
                selected=" selected"
            l.append("""<option value=%s%s>%s</option>"""%(quoteattr(title),
                                        selected, escape(title)))
        return "".join(l)
