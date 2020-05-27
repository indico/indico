# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, redirect, request, session
from werkzeug.exceptions import BadRequest, Forbidden

from indico.core.db import db
from indico.modules.admin import RHAdminBase
from indico.modules.api import APIMode, api_settings
from indico.modules.api.forms import AdminSettingsForm
from indico.modules.api.models.keys import APIKey
from indico.modules.api.views import WPAPIAdmin, WPAPIUserProfile
from indico.modules.categories.models.categories import Category
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.models.events import Event
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.users.controllers import RHUserBase
from indico.util.i18n import _
from indico.web.flask.util import redirect_or_jsonify, url_for
from indico.web.forms.base import FormDefaults
from indico.web.http_api.util import generate_public_auth_request
from indico.web.rh import RH
from indico.web.util import jsonify_data


class RHAPIAdminSettings(RHAdminBase):
    """API settings (admin)"""

    def _process(self):
        form = AdminSettingsForm(obj=FormDefaults(**api_settings.get_all()))
        if form.validate_on_submit():
            api_settings.set_multi(form.data)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.admin_settings'))
        count = APIKey.find(is_active=True).count()
        return WPAPIAdmin.render_template('admin_settings.html', form=form, count=count)


class RHAPIAdminKeys(RHAdminBase):
    """API key list (admin)"""

    def _process(self):
        keys = sorted(APIKey.find_all(is_active=True), key=lambda ak: (ak.use_count == 0, ak.user.full_name))
        return WPAPIAdmin.render_template('admin_keys.html', keys=keys)


class RHUserAPIBase(RHUserBase):
    """Base class for user API management"""

    allow_system_user = True


class RHAPIUserProfile(RHUserAPIBase):
    """API key details (user)"""

    def _process(self):
        key = self.user.api_key
        use_signatures = api_settings.get('security_mode') in {APIMode.SIGNED, APIMode.ONLYKEY_SIGNED,
                                                               APIMode.ALL_SIGNED}
        allow_persistent = api_settings.get('allow_persistent')
        old_keys = self.user.old_api_keys
        return WPAPIUserProfile.render_template('user_profile.html', 'api',
                                                user=self.user, key=key, old_keys=old_keys,
                                                use_signatures=use_signatures, allow_persistent=allow_persistent,
                                                can_modify=(not key or not key.is_blocked or session.user.is_admin))


class RHAPICreateKey(RHUserAPIBase):
    """API key creation"""

    def _process(self):
        quiet = request.form.get('quiet') == '1'
        force = request.form.get('force') == '1'
        persistent = request.form.get('persistent') == '1' and api_settings.get('allow_persistent')
        old_key = self.user.api_key
        if old_key:
            if not force:
                raise BadRequest('There is already an API key for this user')
            if old_key.is_blocked and not session.user.is_admin:
                raise Forbidden
            old_key.is_active = False
            db.session.flush()
        key = APIKey(user=self.user)
        db.session.add(key)
        if persistent:
            key.is_persistent_allowed = persistent
        elif old_key:
            key.is_persistent_allowed = old_key.is_persistent_allowed
        if not quiet:
            if old_key:
                flash(_('Your API key has been successfully replaced.'), 'success')
                if old_key.use_count:
                    flash(_('Please update any applications which use old key.'), 'warning')
            else:
                flash(_('Your API key has been successfully created.'), 'success')
        db.session.flush()
        return redirect_or_jsonify(url_for('api.user_profile'), flash=not quiet,
                                   is_persistent_allowed=key.is_persistent_allowed)


class RHAPIDeleteKey(RHUserAPIBase):
    """API key deletion"""

    def _process(self):
        key = self.user.api_key
        key.is_active = False
        flash(_('Your API key has been deleted.'), 'success')
        return redirect(url_for('api.user_profile'))


class RHAPITogglePersistent(RHUserAPIBase):
    """API key - persistent signatures on/off"""

    def _process(self):
        quiet = request.form.get('quiet') == '1'
        key = self.user.api_key
        key.is_persistent_allowed = api_settings.get('allow_persistent') and request.form['enabled'] == '1'
        if not quiet:
            if key.is_persistent_allowed:
                flash(_('You can now use persistent signatures.'), 'success')
            else:
                flash(_('Persistent signatures have been disabled for your API key.'), 'success')
        return redirect_or_jsonify(url_for('api.user_profile'), flash=not quiet, enabled=key.is_persistent_allowed)


class RHAPIBlockKey(RHUserAPIBase):
    """API key blocking/unblocking"""

    def _check_access(self):
        RHUserAPIBase._check_access(self)
        if not session.user.is_admin:
            raise Forbidden

    def _process(self):
        key = self.user.api_key
        key.is_blocked = not key.is_blocked
        if key.is_blocked:
            flash(_('The API key has been blocked.'), 'success')
        else:
            flash(_('The API key has been unblocked.'), 'success')
        return redirect(url_for('api.user_profile'))


class RHAPIBuildURLs(RH):
    def _process_args(self):
        data = request.json
        self.object = None
        if 'categId' in data:
            self.object = Category.get_or_404(data['categId'])
        elif 'contribId' in data:
            self.object = Contribution.get_or_404(data['contribId'])
        elif 'sessionId' in data:
            self.object = Session.get_or_404(data['sessionId'])
        elif 'confId' in data:
            self.object = Event.get_or_404(data['confId'])

        if self.object is None:
            raise BadRequest

    def _process(self):
        urls = {}
        api_key = session.user.api_key if session.user else None
        url_format = '/export/event/{0}/{1}/{2}.ics'
        if isinstance(self.object, Contribution):
            event = self.object.event
            urls = generate_public_auth_request(api_key, url_format.format(event.id, 'contribution', self.object.id))
        elif isinstance(self.object, Session):
            event = self.object.event
            urls = generate_public_auth_request(api_key, url_format.format(event.id, 'session', self.object.id))
        elif isinstance(self.object, Category):
            urls = generate_public_auth_request(api_key, '/export/categ/{0}.ics'.format(self.object.id),
                                                {'from': '-31d'})
        elif isinstance(self.object, Event):
            urls = generate_public_auth_request(api_key, '/export/event/{0}.ics'.format(self.object.id))
            event_urls = generate_public_auth_request(api_key, '/export/event/{0}.ics'.format(self.object.id),
                                                      {'detail': 'contribution'})
            urls['publicRequestDetailedURL'] = event_urls['publicRequestURL']
            urls['authRequestDetailedURL'] = event_urls['authRequestURL']
        return jsonify_data(flash=False, urls=urls)
