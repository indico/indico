# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pickle
import uuid
from datetime import datetime, timedelta

from flask import current_app, request
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict
from werkzeug.utils import cached_property

from indico.core.cache import make_scoped_cache
from indico.core.config import config
from indico.modules.users import User
from indico.util.date_time import get_display_tz
from indico.util.i18n import set_best_lang
from indico.web.util import get_request_user


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
    @property
    def user(self):
        return get_request_user()[0]

    def set_session_user(self, user):
        """Set the user logged in via this session."""
        if not current_app.testing:
            # Sanity check since logging in via the session during a request authenticated
            # via token/oauth never makes sense. Disabled during testing since we usually
            # know what we're doing there.
            current_user, source = get_request_user()
            if current_user is not None and source != 'session':
                raise Exception('Cannot set session user while authenticated using other means')

        if user is None:
            self.pop('_user_id', None)
        else:
            self['_user_id'] = user.id
        self._refresh_sid = True

    def get_session_user(self):
        """Get the user logged in via this session."""
        user_id = self.get('_user_id')
        return User.get(user_id) if user_id is not None else None

    @property
    def lang(self):
        return self.get('_lang') or set_best_lang(check_session=False)

    @lang.setter
    def lang(self, lang):
        self['_lang'] = lang

    @property
    def moment_lang(self):
        parts = self.lang.lower().split('_')  # e.g. `en_GB` or `zh_Hans_CN`
        lang = parts[0]
        territory = parts[-1]
        if lang == territory or lang == 'uk' or self.lang == 'en_US':
            # TODO we should add some metadata that stores the canonical locale name and
            # the name of the moment locale to avoid hacks like the one here. for example,
            # fr_FR is handled somewhat nicely, but ukrainian (uk_UA) needs an explicit check
            # since it's a single-country locale but locale and territory name are different..
            # `setMomentLocale` in JS has the same problem, so any fix here should be applied
            # over there as well.
            return lang
        else:
            return f'{lang}-{territory}'

    @cached_property
    def csrf_token(self):
        if '_csrf_token' not in self:
            if not self.csrf_protected:
                # don't store a token in the session if we don't really need CSRF protection
                return '00000000-0000-0000-0000-000000000000'
            self['_csrf_token'] = str(uuid.uuid4())
        return self['_csrf_token']

    @property
    def csrf_protected(self):
        # Protect auth endpoints to prevent CSRF login attacks
        return self.user is not None or request.blueprint == 'auth'

    @property
    def timezone(self):
        if '_timezone' in self:
            return self['_timezone']
        if '_user_id' not in self:
            return 'LOCAL'
        return config.DEFAULT_TIMEZONE

    @timezone.setter
    def timezone(self, tz):
        self['_timezone'] = tz

    @property
    def tzinfo(self):
        """The tzinfo of the user's current timezone.

        This should only be used in places where no other timezone
        such as from an event or category is available.
        """
        return get_display_tz(as_timezone=True)


class IndicoSessionInterface(SessionInterface):
    pickle_based = True
    serializer = pickle
    session_class = IndicoSession
    temporary_session_lifetime = timedelta(days=7)

    def __init__(self):
        self.storage = make_scoped_cache('flask-session')

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

    def should_refresh_sid(self, app, session):
        if not session.new and self.get_cookie_secure(app) and not session.get('_secure'):
            return True
        if getattr(session, '_refresh_sid', False):
            return True
        return False

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            return self.session_class(sid=self.generate_sid(), new=True)
        data = self.storage.get(sid)
        if data is not None:
            try:
                return self.session_class(self.serializer.loads(data), sid=sid)
            except TypeError:
                # fall through to generating a new session; this likely happens when
                # you have a session saved on Python 2
                pass
        return self.session_class(sid=self.generate_sid(), new=True)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        secure = self.get_cookie_secure(app)
        refresh_sid = self.should_refresh_sid(app, session)
        if not session and not session.new:
            # empty session, delete it from storage and cookie
            self.storage.delete(session.sid)
            response.delete_cookie(app.session_cookie_name, domain=domain)
            return

        if not refresh_sid and not session.modified and not self.should_refresh_session(app, session):
            # If the session has not been modified we only store if it needs to be refreshed
            return

        if config.SESSION_LIFETIME > 0:
            # Setting session.permanent marks the session as modified so we only set it when we
            # are saving the session anyway!
            session.permanent = True

        storage_ttl = self.get_storage_lifetime(app, session)
        cookie_lifetime = self.get_expiration_time(app, session)
        session['_expires'] = datetime.now() + storage_ttl

        if refresh_sid:
            self.storage.delete(session.sid)
            session.sid = self.generate_sid()

        session['_secure'] = request.is_secure
        self.storage.set(session.sid, self.serializer.dumps(dict(session)), storage_ttl)
        response.set_cookie(app.session_cookie_name, session.sid, expires=cookie_lifetime, httponly=True,
                            secure=secure)
