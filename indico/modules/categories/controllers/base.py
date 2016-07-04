# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from datetime import datetime
from itertools import groupby
from operator import attrgetter

from dateutil.relativedelta import relativedelta
from flask import request, session
from werkzeug.exceptions import NotFound, Forbidden

from indico.modules.categories.models.categories import Category
from indico.util.date_time import format_date, now_utc
from indico.util.i18n import _
from MaKaC.webinterface.rh.base import RH


class RHCategoryBase(RH):
    CSRF_ENABLED = True

    _category_query_options = ()

    @property
    def _category_query(self):
        query = Category.query
        if self._category_query_options:
            query = query.options(*self._category_query_options)
        return query

    def _checkParams(self):
        category_id = request.view_args['category_id']
        self.category = self._category_query.filter_by(id=category_id, is_deleted=False).one_or_none()
        if self.category is None:
            raise NotFound(_("This category does not exist or has been deleted."))


class RHDisplayCategoryBase(RHCategoryBase):
    """Base class for category display pages"""

    def _checkParams(self):
        RHCategoryBase._checkParams(self)
        self.now = now_utc(exact=False).astimezone(self.category.display_tzinfo)

    def _checkProtection(self):
        if not self.category.can_access(session.user):
            msg = [_("You are not authorized to access this category.")]
            if self.category.no_access_contact:
                msg.append(_("If you believe you should have access, please contact {}")
                           .format(self.category.no_access_contact))
            raise Forbidden(' '.join(msg))

    @staticmethod
    def format_event_date(event):
        day_month = 'dd MMM'
        if event.start_dt.year != event.end_dt.year:
            return '{} - {}'.format(format_date(event.start_dt), format_date(event.end_dt))
        elif (event.start_dt.month != event.end_dt.month) or (event.start_dt.day != event.end_dt.day):
            return '{} - {}'.format(format_date(event.start_dt, day_month), format_date(event.end_dt, day_month))
        else:
            return format_date(event.start_dt, day_month)

    def group_by_month(self, events):
        def _format_tuple(x):
            (year, month), events = x
            return {'name': format_date(datetime(year=year, month=month, day=1), format='MMMM Y'),
                    'events': list(events),
                    'is_current': year == self.now.year and month == self.now.month}
        months = groupby(events, key=attrgetter('start_dt.year', 'start_dt.month'))
        return map(_format_tuple, months)

    def happening_now(self, event):
        return self.now > event.start_dt and self.now < event.end_dt

    def is_recent(self, dt):
        return dt > self.now - relativedelta(weeks=1)


class RHManageCategoryBase(RHCategoryBase):
    def _checkProtection(self):
        if not self.category.can_manage(session.user):
            raise Forbidden
