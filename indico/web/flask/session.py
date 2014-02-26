# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
import uuid
from datetime import datetime, timedelta
from flask import request
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict
from werkzeug.utils import cached_property

from indico.core.db import DBMgr
from MaKaC.common.cache import GenericCache
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.user import AvatarHolder
from indico.util.decorators import cached_writable_property


class BaseSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False
        defaults = self._get_defaults()
        if defaults:
            self.update(defaults)

    def _get_defaults(self):
        # Note: This is called before there is a DB connection available!
        return None


# Hey, if you intend on adding a custom property to this class:
# - Only do it if you need logic behind it. Otherwise use the dict API!
# - Even if you do need logic, keep it to core stuff. Otherwise it probably does not belong here!
# - Always prefix the dict keys backing a property with an underscore (to prevent clashes with externally-set items)
# - When you store something like the avatar that involves a DB lookup, use cached_writable_property
class IndicoSession(BaseSession):
    @cached_writable_property('_avatar')
    def user(self):
        avatarId = self.get('_avatarId')
        if not avatarId:
            return None
        return AvatarHolder().getById(avatarId)

    @user.setter
    def user(self, avatar):
        if avatar is None:
            self.pop('_avatarId', None)
        else:
            self['_avatarId'] = avatar.getId()

    @property
    def lang(self):
        if '_lang' in self:
            return self['_lang']
        elif self.user:
            return self.user.getLang()
        else:
            with DBMgr.getInstance().global_connection():
                return HelperMaKaCInfo.getMaKaCInfoInstance().getLang()

    @lang.setter
    def lang(self, lang):
        self['_lang'] = lang

    @cached_property
    def csrf_token(self):
        if not self.csrf_protected:
            return ''
        if '_csrf_token' not in self:
            self['_csrf_token'] = str(uuid.uuid4())
        return self['_csrf_token']

    @property
    def csrf_protected(self):
        return self.user is not None

    @property
    def timezone(self):
        if '_timezone' in self:
            return self['_timezone']
        if '_avatarId' not in self:
            return 'LOCAL'
        with DBMgr.getInstance().global_connection():
            return HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()

    @timezone.setter
    def timezone(self, tz):
        self['_timezone'] = tz


class IndicoSessionInterface(SessionInterface):
    pickle_based = True
    serializer = cPickle
    session_class = IndicoSession
    temporary_session_lifetime = timedelta(days=7)

    def __init__(self):
        self.storage = GenericCache('flask-session')

    def generate_sid(self):
        return str(uuid.uuid4())

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

    def should_refresh_session(self, app, session):
        if session.new or '_expires' not in session:
            return False
        threshold = self.get_storage_lifetime(app, session) / 2
        return session['_expires'] - datetime.now() < threshold

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
        if not session and not session.new:
            # empty session, delete it from storage and cookie
            self.storage.delete(session.sid)
            response.delete_cookie(app.session_cookie_name, domain=domain)
            return

        if not session.modified and not self.should_refresh_session(app, session):
            # If the session has not been modified we only store if it needs to be refreshed
            return

        if app.config['INDICO_SESSION_PERMANENT']:
            # Setting session.permanent marks the session as modified so we only set it when we
            # are saving the session anyway!
            session.permanent = True

        storage_ttl = self.get_storage_lifetime(app, session)
        cookie_lifetime = self.get_expiration_time(app, session)
        session['_expires'] = datetime.now() + storage_ttl

        self.storage.set(session.sid, self.serializer.dumps(dict(session)), storage_ttl)
        response.set_cookie(app.session_cookie_name, session.sid, expires=cookie_lifetime, httponly=True,
                            secure=self.get_cookie_secure(app))
