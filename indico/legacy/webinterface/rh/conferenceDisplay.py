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

from flask import flash, request, session
from werkzeug.exceptions import Forbidden

from indico.legacy.webinterface.rh.conferenceBase import RHConferenceBase
from indico.modules.events.legacy import LegacyConference
from indico.modules.events.views import WPAccessKey
from indico.util.i18n import _


class AccessKeyRequired(Forbidden):
    pass


class RHConferenceBaseDisplay(RHConferenceBase):
    def _forbidden_if_not_admin(self):
        if not request.is_xhr and session.user and session.user.is_admin:
            flash(_('This page is currently not visible by non-admin users (menu entry disabled)!'), 'warning')
        else:
            raise Forbidden

    def _check_access(self):
        if not isinstance(self._target, LegacyConference):
            raise Exception('Unexpected object')
        if self.event.can_access(session.user):
            return
        elif self.event.access_key:
            raise AccessKeyRequired
        elif session.user is None:
            raise Forbidden
        else:
            msg = [_("You are not authorized to access this event.")]
            if self.event.no_access_contact:
                msg.append(_("If you believe you should have access, please contact {}")
                           .format(self.event.no_access_contact))
            raise Forbidden(' '.join(msg))

    def _show_access_key_form(self):
        return WPAccessKey.render_template('display/access_key.html', event=self.event)

    def _do_process(self):
        try:
            return RHConferenceBase._do_process(self)
        except AccessKeyRequired:
            return self._show_access_key_form()
