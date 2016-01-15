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

from flask import request, jsonify, session
from werkzeug.exceptions import BadRequest

from indico.modules.events import EventLogRealm, EventLogKind
from indico.modules.events.sessions import session_settings, COORDINATOR_PRIV_SETTINGS, COORDINATOR_PRIV_TITLES
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHSessionCoordinatorPrivs(RHConferenceModifBase):
    """RESTful management of session coordinator privileges"""

    CSRF_ENABLED = True

    def _process(self):
        # ConferenceModifBase overrides this with functionality that
        # doesn't even belong in there...
        return RH._process(self)

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.priv = request.view_args.get('priv')

    def _get_priv_setting(self):
        try:
            return COORDINATOR_PRIV_SETTINGS[self.priv]
        except KeyError:
            raise BadRequest('No such privilege')

    def _process_GET(self):
        settings = session_settings.get_all(self.event_new)
        return jsonify(privs=[name for name, setting in COORDINATOR_PRIV_SETTINGS.iteritems() if settings[setting]])

    def _process_PUT(self):
        setting = self._get_priv_setting()
        if not session_settings.get(self.event_new, setting):
            session_settings.set(self.event_new, setting, True)
            self.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Protection',
                               'Session coordinator privilege granted: {}'.format(COORDINATOR_PRIV_TITLES[self.priv]),
                               session.user)
        return jsonify(enabled=True)

    def _process_DELETE(self):
        setting = self._get_priv_setting()
        if session_settings.get(self.event_new, setting):
            session_settings.set(self.event_new, setting, False)
            self.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Protection',
                               'Session coordinator privilege revoked: {}'.format(COORDINATOR_PRIV_TITLES[self.priv]),
                               session.user)
        return jsonify(enabled=False)
