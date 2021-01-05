# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import re

import requests
from flask import flash, jsonify, redirect, request, session
from packaging.version import Version
from pkg_resources import DistributionNotFound, get_distribution
from pytz import common_timezones_set
from webargs import fields
from werkzeug.exceptions import BadRequest, NotFound, ServiceUnavailable
from werkzeug.urls import url_join, url_parse

import indico
from indico.core.config import config
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.errors import NoReportError, UserValueError
from indico.core.logger import Logger
from indico.core.notifications import make_email, send_email
from indico.core.settings import PrefixSettingsProxy
from indico.modules.admin import RHAdminBase
from indico.modules.cephalopod import cephalopod_settings
from indico.modules.core.forms import SettingsForm
from indico.modules.core.settings import core_settings, social_settings
from indico.modules.core.views import WPContact, WPSettings
from indico.modules.legal import legal_settings
from indico.modules.users.controllers import RHUserBase
from indico.util.i18n import _, get_all_locales
from indico.util.marshmallow import PrincipalDict
from indico.util.string import sanitize_html
from indico.web.args import use_kwargs
from indico.web.errors import load_error_data
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.rh import RH, RHProtected
from indico.web.util import signed_url_for


class RHContact(RH):
    def _process(self):
        if not config.PUBLIC_SUPPORT_EMAIL:
            raise NotFound
        return WPContact.render_template('contact.html')


class RHReportErrorAPI(RH):
    def _process_args(self):
        self.error_data = load_error_data(request.view_args['error_id'])
        if self.error_data is None:
            raise NotFound('Error details not found. We might be having some technical issues; please try again later.')

    def _save_report(self, email, comment):
        self._send_email(email, comment)
        if config.SENTRY_DSN and self.error_data['sentry_event_id'] is not None:
            self._send_sentry(email, comment)

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

    @use_kwargs({
        'email': fields.Email(missing=None),
        'comment': fields.String(required=True),
    })
    def _process(self, email, comment):
        self._save_report(email, comment)
        return '', 204


class RHSettings(RHAdminBase):
    """General settings."""

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
    """Update the session/user timezone."""

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
            if tz and tz in common_timezones_set:
                session.user.settings.set('timezone', tz)

        return '', 204


class RHChangeLanguage(RH):
    """Update the session/user language."""

    def _process(self):
        language = request.form['lang']
        if language not in get_all_locales():
            raise UserValueError('Invalid language')
        session.lang = language
        if session.user:
            session.user.settings.set('lang', language)
        return '', 204


class RHVersionCheck(RHAdminBase):
    """Check the installed indico version against pypi."""

    def _check_version(self, distribution, current_version=None):
        try:
            response = requests.get('https://pypi.org/pypi/{}/json'.format(distribution))
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


class PrincipalsMixin(object):
    def _serialize_principal(self, identifier, principal):
        if principal.principal_type == PrincipalType.user:
            return {'identifier': identifier,
                    'type': 'user',
                    'user_id': principal.id,
                    'invalid': principal.is_deleted,
                    'name': principal.display_full_name,
                    'detail': ('{} ({})'.format(principal.email, principal.affiliation)
                               if principal.affiliation else principal.email)}
        elif principal.principal_type == PrincipalType.local_group:
            return {'identifier': identifier,
                    'type': 'local_group',
                    'invalid': principal.group is None,
                    'name': principal.name}
        elif principal.principal_type == PrincipalType.multipass_group:
            return {'identifier': identifier,
                    'type': 'multipass_group',
                    'invalid': principal.group is None,
                    'name': principal.name,
                    'detail': principal.provider_title}
        elif principal.principal_type == PrincipalType.event_role:
            return {'identifier': identifier,
                    'type': 'event_role',
                    'invalid': False,
                    'name': principal.name,
                    'meta': {'style': principal.style, 'code': principal.code}}
        elif principal.principal_type == PrincipalType.category_role:
            return {'identifier': identifier,
                    'type': 'category_role',
                    'invalid': False,
                    'name': principal.name,
                    'meta': {'style': principal.style, 'code': principal.code},
                    'detail': principal.category.title}
        elif principal.principal_type == PrincipalType.registration_form:
            return {'identifier': identifier,
                    'type': 'registration_form',
                    'invalid': principal.is_deleted,
                    'name': principal.title}
        elif principal.principal_type == PrincipalType.email:
            return {'identifier': identifier,
                    'type': 'email',
                    'invalid': False,
                    'name': principal.name}

    def _process(self):
        return jsonify({identifier: self._serialize_principal(identifier, principal)
                        for identifier, principal in self.values.viewitems()})


class RHPrincipals(PrincipalsMixin, RHProtected):
    """Resolve principal identifiers to their actual objects.

    This is intended for PrincipalListField which needs to be able
    to resolve the identifiers provided to it to something more
    human-friendly.
    """

    @use_kwargs({
        'values': PrincipalDict(allow_groups=True, allow_external_users=True, allow_emails=True, missing={})
    })
    def _process_args(self, values):
        self.values = values


class RHSignURL(RHProtected):
    def _process(self):
        endpoint = request.json.get('endpoint')
        if not endpoint:
            raise BadRequest
        # filter out non-standard args
        url_params = request.json.get('url_params', {})
        url_params = {k: v for k, v in url_params.viewitems() if not k.startswith('_')}
        query_params = request.json.get('query_params', {})
        query_params = {k: v for k, v in query_params.viewitems() if not k.startswith('_')}
        url = signed_url_for(session.user, endpoint, url_params=url_params, _external=True, **query_params)
        Logger.get('url_signing').info("%s signed URL for endpoint '%s' (%s)", session.user, endpoint, url)
        return jsonify(url=url)


class RHResetSignatureTokens(RHUserBase):
    def _process(self):
        self.user.reset_signing_secret()
        flash(_('All your token-based links have been invalidated'), 'success')
        return redirect(url_for('api.user_profile'))


class RHConfig(RH):
    def _process(self):
        tos_url = legal_settings.get('tos_url')
        tos_html = sanitize_html(legal_settings.get('tos')) or None
        privacy_policy_url = legal_settings.get('privacy_policy_url')
        privacy_policy_html = sanitize_html(legal_settings.get('privacy_policy')) or None
        if tos_url:
            tos_html = None
        if privacy_policy_url:
            privacy_policy_html = None

        return jsonify(help_url=config.HELP_URL,
                       contact_email=config.PUBLIC_SUPPORT_EMAIL,
                       has_tos=bool(tos_url or tos_html),
                       tos_html=tos_html,
                       tos_url=tos_url,
                       has_privacy_policy=bool(privacy_policy_url or privacy_policy_html),
                       privacy_policy_html=privacy_policy_html,
                       privacy_policy_url=privacy_policy_url)
