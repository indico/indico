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

from flask import request, jsonify
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import BadRequest, Forbidden

from indico.modules.oauth import oauth
from indico.modules.events.models.events import Event
from indico.modules.events.registration.util import build_registrations_api_data, build_registration_api_data

from indico.legacy.webinterface.rh.base import RH


class RHAPIRegistrant(RH):
    """RESTful registrant API"""

    CSRF_ENABLED = False

    @oauth.require_oauth('registrants')
    def _checkProtection(self):
        if not self.event.can_manage(request.oauth.user, role='registration'):
            raise Forbidden()

    def _checkParams(self):
        self.event = Event.find(id=request.view_args['event_id'], is_deleted=False).first_or_404()
        self._registration = (self.event.registrations
                              .filter_by(id=request.view_args['registrant_id'],
                                         is_deleted=False)
                              .options(joinedload('data').joinedload('field_data'))
                              .first_or_404())

    def _process_GET(self):
        return jsonify(build_registration_api_data(self._registration))

    def _process_PATCH(self):
        if request.json is None:
            raise BadRequest('Expected JSON payload')

        invalid_fields = request.json.viewkeys() - {'checked_in'}
        if invalid_fields:
            raise BadRequest("Invalid fields: {}".format(', '.join(invalid_fields)))

        if 'checked_in' in request.json:
            self._registration.checked_in = bool(request.json['checked_in'])

        return jsonify(build_registration_api_data(self._registration))


class RHAPIRegistrants(RH):
    """RESTful registrants API"""

    @oauth.require_oauth('registrants')
    def _checkProtection(self):
        if not self.event.can_manage(request.oauth.user, role='registration'):
            raise Forbidden()

    def _checkParams(self):
        self.event = Event.find(id=request.view_args['event_id'], is_deleted=False).first_or_404()

    def _process_GET(self):
        return jsonify(registrants=build_registrations_api_data(self.event))
