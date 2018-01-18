# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import re

import requests
from flask import flash, jsonify, redirect, request, session
from packaging.version import Version
from pkg_resources import DistributionNotFound, get_distribution
from pytz import common_timezones_set
from werkzeug.exceptions import NotFound, ServiceUnavailable
from werkzeug.urls import url_join, url_parse

import indico
from indico.core.config import config
from indico.core.errors import NoReportError, UserValueError
from indico.core.logger import Logger
from indico.core.notifications import make_email, send_email
from indico.core.settings import PrefixSettingsProxy
from indico.modules.admin import RHAdminBase
from indico.modules.cephalopod import cephalopod_settings
from indico.modules.core.forms import ReportErrorForm, SettingsForm
from indico.modules.core.settings import core_settings, social_settings
from indico.modules.core.views import WPContact, WPSettings
from indico.util.i18n import _, get_all_locales
from indico.web.errors import load_error_data
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.rh import RH
from indico.web.util import jsonify_data, jsonify_form


class RHContact(RH):
    def _process(self):
        if not config.PUBLIC_SUPPORT_EMAIL:
            raise NotFound
        return WPContact.render_template('contact.html')


class RHReportError(RH):
    NOT_SANITIZED_FIELDS = {'comment'}

    def _process_args(self):
        self.error_data = load_error_data(request.view_args['error_id'])
        if self.error_data is None:
            raise NotFound('Error details not found. We might be having some technical issues; please try again later.')

    def _process(self):
        form = ReportErrorForm(email=(session.user.email if session.user else ''))
        if form.validate_on_submit():
            self._send_email(form.email.data, form.comment.data)
            if config.SENTRY_DSN and self.error_data['sentry_event_id'] is not None:
                self._send_sentry(form.email.data, form.comment.data)
            return jsonify_data(flash=False)
        return jsonify_form(form)

    def _send_email(self, email, comment):
        # using reply-to for the user email would be nicer, but email clients
        # usually only show the from address and it's nice to immediately see
        # whether an error report has an email address associated and if
        # multiple reports came from the same person
        template = get_template_module('core/emails/error_report.txt',
                                       comment=comment,
                                       error_data=self.error_data,
                                       server_name=url_parse(config.BASE_URL).netloc)
        send_email(make_email(config.SUPPORT_EMAIL, from_address=(email or config.NO_REPLY_EMAIL), template=template))

    def _send_sentry(self, email, comment):
        # strip password and query string from the DSN, and all auth data from the POST target
        dsn = re.sub(r':[^@/]+(?=@)', '', config.SENTRY_DSN)
        url = url_parse(dsn)
        dsn = unicode(url.replace(query=None))
        verify = url.decode_query().get('ca_certs', True)
        url = unicode(url.replace(path='/api/embed/error-page/', netloc=url._split_netloc()[1], query=None))
        user_data = self.error_data['request_info']['user'] or {'name': 'Anonymous', 'email': config.NO_REPLY_EMAIL}
        try:
            rv = requests.post(url,
                               params={'dsn': dsn,
                                       'eventId': self.error_data['sentry_event_id']},
                               data={'name': user_data['name'],
                                     'email': email or user_data['email'],
                                     'comments': comment},
                               headers={'Origin': config.BASE_URL},
                               verify=verify)
            rv.raise_for_status()
        except Exception:
            # don't bother users if this fails!
            Logger.get('sentry').exception('Could not submit user feedback')


class RHSettings(RHAdminBase):
    """General settings"""

    def _get_cephalopod_data(self):
        if not cephalopod_settings.get('joined'):
            return None, {'enabled': False}

        url = url_join(config.COMMUNITY_HUB_URL,
                       'api/instance/{}'.format(cephalopod_settings.get('uuid')))
        data = {'enabled': cephalopod_settings.get('joined'),
                'contact': cephalopod_settings.get('contact_name'),
                'email': cephalopod_settings.get('contact_email'),
                'url': config.BASE_URL,
                'organization': core_settings.get('site_organization')}
        return url, data

    def _process(self):
        proxy = PrefixSettingsProxy({'core': core_settings, 'social': social_settings})
        form = SettingsForm(obj=FormDefaults(**proxy.get_all()))
        if form.validate_on_submit():
            proxy.set_multi(form.data)
            flash(_('Settings have been saved'), 'success')
            return redirect(url_for('.settings'))

        cephalopod_url, cephalopod_data = self._get_cephalopod_data()
        show_migration_message = cephalopod_settings.get('show_migration_message')
        return WPSettings.render_template('admin/settings.html', 'settings',
                                          form=form,
                                          core_settings=core_settings.get_all(),
                                          social_settings=social_settings.get_all(),
                                          cephalopod_url=cephalopod_url,
                                          cephalopod_data=cephalopod_data,
                                          show_migration_message=show_migration_message)


class RHChangeTimezone(RH):
    """Update the session/user timezone"""

    def _process(self):
        mode = request.form['tz_mode']
        tz = request.form.get('tz')
        update_user = request.form.get('update_user') == '1'

        if mode == 'local':
            session.timezone = 'LOCAL'
        elif mode == 'user' and session.user:
            session.timezone = session.user.settings.get('timezone', config.DEFAULT_TIMEZONE)
        elif mode == 'custom' and tz in common_timezones_set:
            session.timezone = tz

        if update_user:
            session.user.settings.set('force_timezone', mode != 'local')
            if tz:
                session.user.settings.set('timezone', tz)

        return '', 204


class RHChangeLanguage(RH):
    """Update the session/user language"""

    def _process(self):
        language = request.form['lang']
        if language not in get_all_locales():
            raise UserValueError('Invalid language')
        session.lang = language
        if session.user:
            session.user.settings.set('lang', language)
        return '', 204


class RHVersionCheck(RHAdminBase):
    """Check the installed indico version against pypi"""

    def _check_version(self, distribution, current_version=None):
        try:
            response = requests.get('https://pypi.python.org/pypi/{}/json'.format(distribution))
        except requests.RequestException as exc:
            Logger.get('versioncheck').warning('Version check for %s failed: %s', distribution, exc)
            raise NoReportError.wrap_exc(ServiceUnavailable())
        try:
            data = response.json()
        except ValueError:
            return None
        if current_version is None:
            try:
                current_version = get_distribution(distribution).version
            except DistributionNotFound:
                return None
        current_version = Version(current_version)
        if current_version.is_prerelease:
            # if we are on a prerelease, get the latest one even if it's also a prerelease
            latest_version = Version(data['info']['version'])
        else:
            # if we are stable, get the latest stable version
            versions = [v for v in map(Version, data['releases']) if not v.is_prerelease]
            latest_version = max(versions) if versions else None
        return {'current_version': unicode(current_version),
                'latest_version': unicode(latest_version) if latest_version else None,
                'outdated': (current_version < latest_version) if latest_version else False}

    def _process(self):
        return jsonify(indico=self._check_version('indico', indico.__version__),
                       plugins=self._check_version('indico-plugins'))
