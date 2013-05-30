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
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

import cPickle
from flask import request
import uuid
from datetime import timedelta
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict

from MaKaC.common.cache import GenericCache


class IndicoSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class IndicoSessionInterface(SessionInterface):
    pickle_based = True
    serializer = cPickle
    session_class = IndicoSession
    temporary_session_lifetime = timedelta(days=7)

    def __init__(self):
        self.storage = GenericCache('flask-session')

    def generate_sid(self):
        sid = str(uuid.uuid4())
        # Collisions are VERY unlikely but just to be completely safe we delete any existing session
        self.storage.delete(sid)
        return sid

    def get_cookie_secure(self, app):
        return request.is_secure

    def get_storage_lifetime(self, app, session):
        # Permanent sessions are stored for exactly the same duration as the session id cookie.
        # "Temporary" session are stored for a period that is not too short/long as some people
        # close their browser very rarely and thus shouldn't be logged out that often.
        if session.permanent:
            return app.permanent_session_lifetime
        else:
            return self.temporary_session_lifetime

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            return self.session_class(sid=self.generate_sid(), new=True)
        data = self.storage.get(sid)
        if data is not None:
            return self.session_class(self.serializer.loads(data), sid=sid)
        return self.session_class(sid=self.generate_sid(), new=True)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        if not session:  # empty session, delete it from storage and cookie
            self.storage.delete(session.sid)
            response.delete_cookie(app.session_cookie_name, domain=domain)
            return
        if not session.modified:
            # It might be a good idea to store the expiry time in the session itself.
            # This way we could refresh it from time to time to prevent it from expiring
            # while it's still in use.
            return
        storage_ttl = self.get_storage_lifetime(app, session)
        cookie_lifetime = self.get_expiration_time(app, session)
        self.storage.set(session.sid, self.serializer.dumps(dict(session)), storage_ttl)
        response.set_cookie(app.session_cookie_name, session.sid, expires=cookie_lifetime, httponly=True,
                            secure=self.get_cookie_secure(app))
