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

from MaKaC.services.implementation.base import AdminService
from MaKaC.services.interface.rpc.common import ServiceError, NoReportError
from MaKaC.plugins import PluginsHolder


class CurrencyBase(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        ph = PluginsHolder()
        self._targetOption = ph.getPluginType('EPayment').getOption("customCurrency")
        self._currencyName = self._params.get('name', None)
        self._currencies = self._targetOption.getValue()

    def _getAnswer(self):
        return {'success': self._process(),
                'table': self._currencies}

    def _findCurrency(self, name):
        for currency in self._currencies:
            if currency['name'] == name:
                return currency
        return None


class AddCurrency(CurrencyBase):

    def _checkParams(self):
        CurrencyBase._checkParams(self)
        self._currencyAbbreviation = self._params.get('abbreviation', None)

    def _process(self):
        if self._findCurrency(self._currencyName):
            return False
        else:
            self._currencies.append({'name': self._currencyName, 'abbreviation': self._currencyAbbreviation})
            self._targetOption.setValue(self._targetOption.getValue())
            self._targetOption._notifyModification()
            return True


class RemoveCurrency(CurrencyBase):

    def _process(self):
        currency = self._findCurrency(self._currencyName)
        if currency:
            self._currencies.remove(currency)
            self._targetOption._notifyModification()
            return True
        else:
            return False


class EditCurrency(CurrencyBase):

    def _checkParams(self):
        CurrencyBase._checkParams(self)
        self._currencyAbbreviation = self._params.get('abbreviation', None)
        self._currencyOldName = self._params.get('oldName', None)

    def _process(self):
        currency = self._findCurrency(self._currencyOldName)

        if currency:
            currency.update({'name': self._currencyName,
                             'abbreviation': self._currencyAbbreviation})
            self._targetOption.setValue(self._targetOption.getValue())
            self._targetOption._notifyModification()
            return True
        else:
            return False


methodMap = {
    "epayment.addCurrency": AddCurrency,
    "epayment.removeCurrency": RemoveCurrency,
    "epayment.editCurrency": EditCurrency
}
