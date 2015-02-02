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

from indico.core.errors import AccessError
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


class RHRequestsEventRequestDetailsBase(RHRequestsEventRequestBase):
    """Base class for the details/edit/manage views of a specific request"""

    def _process(self):
        is_manager = self.definition.can_manage(session.user)

        self.form = form = self.definition.create_form(self.request)
        self.manager_form = manager_form = self.definition.create_manager_form(self.request) if self.request else None
        rv = self.process_form()
        if rv:
            return rv

        form_html = self.definition.render_form(event=self.event, definition=self.definition, req=self.request,
                                                form=form, is_manager=is_manager, manager_form=manager_form)
        return WPRequestsEventManagement.render_string(form_html, self.event)

    def process_form(self):
        raise NotImplementedError


class RHRequestsEventRequestDetails(RHRequestsEventRequestDetailsBase):
    """Details/form for a specific request"""

    _require_request = False

    def process_form(self):
        form = self.form
        if not form.validate_on_submit():
            return
        if not self.request or not self.request.can_be_modified:
            req = Request(event=self.event, definition=self.definition, created_by_user=session.user)
            new = True
        else:
            req = self.request
            new = False
        self.definition.send(req, form.data)
        if new:
            flash_msg = _("Your request ({0}) has been sent. "
                          "You will be notified by e-mail once it has been accepted or rejected.")
        else:
            flash_msg = _("Your request ({0}) has been modified. "
                          "You will be notified by e-mail once it has been accepted or rejected.")
        flash(flash_msg.format(self.definition.title), 'success')
        return redirect(url_for('.event_requests', self.event))


class RHRequestsEventRequestProcess(RHRequestsEventRequestDetailsBase):
    """Process a request"""

    def _checkProtection(self):
        self._checkSessionUser()
        if self._doProcess and not self.definition.can_manage(session.user):
            raise AccessError()

    def process_form(self):
        form = self.manager_form
        if not form.validate_on_submit():
            # This is *very* unlikely to happen, at least with the default form.
            return
        self.request.comment = form.comment.data
        self.definition.process(self.request, form.state.data, form.data, session.user)
        flash('You have successfully processed this request. It is now {0}.'.format(self.request.state.title.lower()),
              'info')
        return redirect(url_for('.event_requests_details', self.request))


class RHRequestsEventRequestWithdraw(RHRequestsEventRequestBase):
    """Withdraw a request"""

    def _process(self):
        if self.request.state not in {RequestState.pending, RequestState.accepted}:
            raise BadRequest
        self.definition.withdraw(self.request)
        flash(_('You have withdrawn your request ({0})').format(self.definition.title))
        return jsonify(success=True, url=url_for('.event_requests', self.event))
