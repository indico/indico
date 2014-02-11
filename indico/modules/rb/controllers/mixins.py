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

from datetime import datetime as DT

from indico.core.errors import NoReportError
from indico.util.i18n import _

from ..models.utils import (
    get_checked_param_dict,
    is_false_valued_dict,
    is_none_valued_dict
)


class RoomBookingAvailabilityParamsMixin:

    def _checkParamsRepeatingPeriod(self, f):
        """
        Extracts startDT, endDT and repeatability
        from the form, if present.

        Assigns these values to self, or Nones if values
        are not present.
        """
        # time
        times = get_checked_param_dict(f, ['sTime', 'eTime'])
        is_time_supplied = not is_false_valued_dict(times)
        if is_time_supplied:
            try:
                times = dict((k, DT.strptime(v, '%H:%M').time()) for k, v in times.items())
            except ValueError:
                raise NoReportError(_('The Start Time must be of the form \'HH:MM\''
                                      ' and must be a valid time.'))

        # date
        date_keys = [i+j for i in 's e'.split() for j in 'Year Month Day'.split()]
        dates = get_checked_param_dict(f, date_keys, converter=int)
        is_date_supplied = not is_none_valued_dict(dates)
        def get_date_from_dict(initial):
            return DT(*(dates[initial + p] for p in 'Year Month Day'.split())).date()

        # combine date and time
        self._today = f.get('day') == 'today'
        self._start_date = self._end_date = None
        if is_date_supplied and is_time_supplied:
            self._start_date = DT.combine(get_date_from_dict('s'), times['sTime'])
            self._end_date = DT.combine(get_date_from_dict('e'), times['eTime'])
        elif is_date_supplied:
            self._start_date = DT.combine(get_date_from_dict('s'), DT.min.time())
            self._end_date = DT.combine(get_date_from_dict('e'), DT.max.time())
        elif is_time_supplied:
            self._start_date = DT.combine(DT.min.date(), times['sTime'])
            self._end_date = DT.combine(DT.max.date(), times['eTime'])
        elif self._today:
            self._start_date = DT.combine(DT.today().date(), DT.min.time())
            self._end_date = DT.combine(DT.today().date(), DT.max.time())

        # repeat
        self._repeatability = get_checked_param_dict(f, ['repeat_unit', 'repeat_step'], converter=int)


class AttributeSetterMixin():

    """ Utility class to make retrieval of parameters from requests """

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
