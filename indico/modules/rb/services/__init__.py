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

from indico.util.date_time import get_datetime_from_request, format_date, is_weekend
from indico.util.i18n import _
from indico.modules.rb.models.holidays import Holiday
from MaKaC.services.implementation.base import ServiceBase


class GetDateWarning(ServiceBase):
    UNICODE_PARAMS = True

    def _checkParams(self):
        self._start_dt = get_datetime_from_request(prefix='start_', source=self._params)
        self._end_dt = get_datetime_from_request(prefix='end_', source=self._params)

    def _getAnswer(self):
        if not self._start_dt or not self._end_dt:
            return None
        start_date = self._start_dt.date()
        end_date = self._end_dt.date()
        holidays = Holiday.find_all(Holiday.date.in_([start_date, end_date]))
        if holidays:
            return _(u'Holidays chosen: {0}'.format(', '.join(h.name or format_date(h.date) for h in holidays)))
        if is_weekend(start_date) or is_weekend(end_date):
            return _(u'Weekend chosen')
        return None
