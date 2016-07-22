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

from datetime import time, datetime

from dateutil.relativedelta import relativedelta
from flask import redirect, request
from pytz import timezone

from indico.core.config import Config
from indico.modules.categories import Category
from indico.modules.events.forms import EventCreationForm
from indico.modules.events.models.events import EventType
from indico.modules.events.operations import create_event
from indico.util.date_time import now_utc
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import url_for_index, jsonify_data, jsonify_template
from MaKaC.webinterface.rh.base import RHProtected


class RHCreateEvent(RHProtected):
    """Create a new event"""

    CSRF_ENABLED = True

    def _checkParams(self):
        self.event_type = EventType[request.view_args['event_type']]

    def _get_form_defaults(self):
        tzinfo = timezone(Config.getInstance().getDefaultTimezone())

        try:
            category_id = int(request.args['category_id'])
        except (ValueError, KeyError):
            category = None
        else:
            category = Category.get(category_id, is_deleted=False)
            if category is not None:
                tzinfo = timezone(category.timezone)

        # try to find good dates/times
        now = now_utc(exact=False)
        start_dt = now + relativedelta(hours=1, minute=0)
        if start_dt.astimezone(tzinfo).time() > time(18):
            start_dt = tzinfo.localize(datetime.combine(now.date() + relativedelta(days=1), time(9)))
        end_dt = start_dt + relativedelta(hours=2)

        # XXX: Do not provide a default value for protection_mode. It is selected via JavaScript code
        # once a category has been selected.
        return FormDefaults(category=category, timezone=tzinfo.zone, start_dt=start_dt, end_dt=end_dt,
                            location_data={'inheriting': False})

    def _process(self):
        if not request.is_xhr:
            return redirect(url_for_index(_anchor='create-event:{}'.format(self.event_type.name)))
        form = EventCreationForm(obj=self._get_form_defaults(), prefix='event-creation-')
        if form.validate_on_submit():
            data = form.data
            event = create_event(data.pop('category'), self.event_type, data)
            return jsonify_data(flash=False, redirect=url_for('event_mgmt.conferenceModification', event))
        return jsonify_template('events/forms/event_creation_form.html', form=form, fields=form._field_order)
