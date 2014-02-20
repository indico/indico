# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

from datetime import datetime

from MaKaC.common.utils import HolidaysHolder
from MaKaC.services.implementation.base import ServiceBase
from MaKaC.services.interface.rpc.common import ServiceError

from indico.util.i18n import _

from ..models.utils import is_weekend


class GetDateWarning(ServiceBase):

    def _checkParams(self):
        self._start_date = datetime.strptime(
            '{} {}'.format(self._params.get('start_date'),
                           self._params.get('start_time')), '%d-%m-%Y %H:%M')
        self._end_date = datetime.strptime(
            '{} {}'.format(self._params.get('end_date'),
                           self._params.get('end_time')), '%d-%m-%Y %H:%M')

    def _getAnswer(self):
        if not self._start_date or not self._end_date or \
           (HolidaysHolder.isWorkingDay(self._start_date) and
            HolidaysHolder.isWorkingDay(self._end_date)):
            return ''

        if is_weekend(self._start_date) or is_weekend(self._end_date):
            return _('weekend chosen')

        return _('holidays chosen')
