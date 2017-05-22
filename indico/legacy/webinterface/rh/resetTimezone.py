# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from flask import redirect, request, session

from indico.core.config import Config
from indico.legacy.webinterface.rh.base import RH
from indico.util.string import to_unicode
from indico.web.util import url_for_index


class RHResetTZ(RH):
    def _process(self):
        if 'activeTimezone' not in request.values or request.values['activeTimezone'] == 'My':
            tz = Config.getInstance().getDefaultTimezone()
            if session.user:
                tz = session.user.settings.get('timezone', tz)
        else:
            tz = request.values['activeTimezone']

        if request.values.get('saveToProfile') == 'on' and session.user:
            if tz == 'LOCAL':
                session.user.settings.set('force_timezone', False)
            else:
                session.user.settings.set('force_timezone', True)
                session.user.settings.set('timezone', to_unicode(tz))

        session.timezone = tz
        return redirect(request.referrer or url_for_index())
