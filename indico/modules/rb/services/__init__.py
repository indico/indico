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
from time import strptime

from MaKaC.services.implementation.base import ServiceBase
from MaKaC.services.interface.rpc.common import ServiceError

from MaKaC.common.utils import HolidaysHolder

from indico.core.errors import NoReportError
from indico.util.i18n import _

from ..models.utils import is_weekend

# TODO
class GetDateWarning(ServiceBase):

    def _checkParams(self):
        """
        Extracts startDT, endDT and repeatability
        from the form, if present.

        Assigns these values to self, or Nones if values
        are not present.
        """

        if self._params.get('day') == 'today':
            self._today = True
            self._startDT = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            self._endDT = self._startDT.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            self._today = False

            for param in ['sDay', 'eDay', 'sMonth', 'eMonth', 'sYear', 'eYear', 'sTime', 'eTime']:
                val = self._params.get(param)
                if val and val.strip():
                    val = val.strip()
                    if not param.endswith('Time'):
                        val = int(val)
                locals()[param] = val

            # process sTime and eTime
            if sTime and eTime:
                for param in ['sTime', 'eTime']:
                    try:
                        locals()[param[0] + 'Hour'], locals()[param[0] + 'Minute'] = map(int, strptime(locals()[param], '%H:%M').split(':'))
                    except ValueError:
                        raise NoReportError(
                            _('{0} must be of the form HH:MM and must be a valid time.').format(
                                _('The Start Time') if param == 'sTime' else _('The End Time')
                            )
                        )


            self._startDT, self._endDT = None, None
            if sYear and sMonth and sDay and sTime and eYear and eMonth and eDay and eTime:
                # Full period specified
                self._startDT = datetime(sYear, sMonth, sDay, sHour, sMinute)
                self._endDT = datetime(eYear, eMonth, eDay, eHour, eMinute)
            elif sYear and sMonth and sDay and eYear and eMonth and eDay:
                # There are no times
                self._startDT = datetime(sYear, sMonth, sDay, 0, 0, 0)
                self._endDT = datetime(eYear, eMonth, eDay, 23, 59, 59)
            elif sTime and eTime:
                # There are no dates
                self._startDT = datetime(1990, 1, 1, sHour, sMinute)
                self._endDT = datetime(2030, 12, 31, eHour, eMinute)

    def _getAnswer(self):
        if not self._startDT or not self._endDT or \
           (HolidaysHolder.isWorkingDay(self._startDT) and HolidaysHolder.isWorkingDay(self._endDT)):
            return ''

        if isWeekend(self._startDT) or isWeekend(self._endDT):
            return _('weekend chosen')

        return _('holidays chosen')
