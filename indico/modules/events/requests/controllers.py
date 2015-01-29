# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import request, jsonify, flash, redirect, session
from werkzeug.exceptions import NotFound, BadRequest

from indico.modules.events.requests import get_request_definitions
from indico.modules.events.requests.models.requests import Request, RequestState
from indico.modules.events.requests.views import WPRequestsEventManagement
from indico.util.i18n import _
from indico.web.flask.util import url_for
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHRequestsEventRequests(RHConferenceModifBase):
    """Overview of existing requests (event)"""

    def _process(self):
        event = self._conf
        definitions = get_request_definitions()
        if not definitions:
            raise NotFound
        requests = Request.find_latest_for_event(self._conf)
        return WPRequestsEventManagement.render_template('event_requests.html', event, event=event,
                                                         definitions=definitions, requests=requests)


class RHRequestsEventRequestBase(RHConferenceModifBase):
    """Base class for pages handling a specific request type"""

    #: if a request must be present in the database
    _require_request = True

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.event = self._conf
        try:
            self.definition = get_request_definitions()[request.view_args['type']]
        except KeyError:
            raise NotFound
        self.request = Request.find_latest_for_event(self.event, self.definition.name)
        if self._require_request and not self.request:
            raise NotFound


class RHRequestsEventRequestDetails(RHRequestsEventRequestBase):
    """Details/form for a specific request"""

    _require_request = False

    def _process(self):
        form = self.definition.create_form(self.request)
        if form.validate_on_submit():
            if not self.request or not self.request.can_be_modified:
                req = Request(event=self.event, definition=self.definition, created_by_user=session.user)
                new = True
            else:
                req = self.request
                new = False
            req.data = form.data
            req.send()
            if new:
                flash_msg = _("Your request ({0}) has been sent. "
                              "You will be notified by e-mail once it has been accepted or rejected.")
            else:
                flash_msg = _("Your request ({0}) has been modified. "
                              "You will be notified by e-mail once it has been accepted or rejected.")
            flash(flash_msg.format(self.definition.title), 'success')
            return redirect(url_for('.event_requests', self.event))

        form_html = self.definition.render_form(event=self.event, definition=self.definition, request=self.request,
                                                form=form)
        return WPRequestsEventManagement.render_string(form_html, self.event)


class RHRequestsEventRequestWithdraw(RHRequestsEventRequestBase):
    """Withdraw a request"""

    def _process(self):
        if self.request.state not in {RequestState.pending, RequestState.accepted}:
            raise BadRequest
        self.request.withdraw()
        flash(_('You have withdrawn your request ({0})').format(self.definition.title))
        return jsonify(success=True, url=url_for('.event_requests', self.event))
