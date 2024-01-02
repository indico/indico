# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from contextlib import ExitStack

from flask import flash, redirect, request, session
from werkzeug.exceptions import Forbidden, NotFound

from indico.modules.events import Event
from indico.modules.events.registration.util import get_event_regforms_registrations
from indico.modules.events.views import WPAccessKey
from indico.modules.logs.models.entries import EventLogRealm, LogKind
from indico.modules.logs.util import make_diff_log
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.rh import RH
from indico.web.util import jsonify_data, jsonify_form


class RHEventBase(RH):
    def _process_args(self):
        self.event = Event.get(request.view_args['event_id'])
        if self.event is None:
            raise NotFound(_('An event with this ID does not exist.'))
        elif self.event.is_deleted:
            raise NotFound(_('This event has been deleted.'))


class RHProtectedEventBase(RHEventBase):
    """
    Base class for events that checks if the user can access it.

    This includes unauthenticated users who have access to the event
    for any other reason (e.g. due to a whitelisted IP address), but
    """

    def _check_access(self):
        if not self.event.can_access(session.user):
            raise Forbidden


class RHAuthenticatedEventBase(RHProtectedEventBase):
    """
    Base class for events that checks if the user is authenticated and
    can access the event.
    """

    def _check_access(self):
        if session.user is None:
            raise Forbidden
        RHProtectedEventBase._check_access(self)


class RHDisplayEventBase(RHProtectedEventBase):
    def __init__(self):
        RHProtectedEventBase.__init__(self)
        self.event_rh_contexts = ExitStack()

    def _forbidden_if_not_admin(self):
        if not request.is_xhr and session.user and session.user.is_admin:
            flash(_('This page is currently not visible by non-admin users (menu entry disabled)!'), 'warning')
        else:
            raise Forbidden

    def _check_access(self):
        try:
            RHProtectedEventBase._check_access(self)
        except Forbidden:
            if self.event.access_key:
                raise AccessKeyRequired
            elif self.event.has_regform_in_acl and self.event.public_regform_access:
                raise RegistrationRequired

            msg = [_('You are not authorized to access this event.')]
            if self.event.no_access_contact:
                msg.append(_('If you believe you should have access, please contact {}')
                           .format(self.event.no_access_contact))
            raise Forbidden(' '.join(msg))

    def _show_access_key_form(self):
        return WPAccessKey.render_template('display/access_key.html', event=self.event)

    def _show_registration_form(self):
        displayed_regforms = get_event_regforms_registrations(self.event, session.user)[0]
        if displayed_regforms and all(r.require_login for r in displayed_regforms) and not session.user:
            # force the user to log in first. like this they will go back to the page they tried to
            # originally access in case they are already registered for the event
            raise Forbidden
        if len(displayed_regforms) == 1:
            return redirect(url_for('event_registration.display_regform', displayed_regforms[0]))
        return redirect(url_for('event_registration.display_regform_list', self.event))

    def _process_args(self):
        RHProtectedEventBase._process_args(self)
        if not getattr(self, 'management', False) and self.event.default_locale:
            self.event_rh_contexts.enter_context(self.event.force_event_locale(session.user, allow_session=True))

    def _do_process(self):
        with self.event_rh_contexts:
            try:
                return RHEventBase._do_process(self)
            except AccessKeyRequired:
                return self._show_access_key_form()
            except RegistrationRequired:
                if request.is_xhr:
                    raise
                return self._show_registration_form()


class EditEventSettingsMixin:
    settings_proxy = None
    form_cls = None
    success_message = None
    log_module = None
    log_message = None
    log_fields = None

    def _process(self):
        current_settings = self.settings_proxy.get_all(self.event)
        form = self.form_cls(obj=FormDefaults(**current_settings))
        if form.validate_on_submit():
            self.settings_proxy.set_multi(self.event, form.data)
            new_settings = self.settings_proxy.get_all(self.event)
            flash(self.success_message, 'success')
            changes = {k: (v, new_settings[k]) for k, v in current_settings.items() if v != new_settings[k]}
            if changes:
                self.event.log(EventLogRealm.management, LogKind.change, self.log_module, self.log_message,
                               session.user, data={'Changes': make_diff_log(changes, self.log_fields)})
            return jsonify_data()
        return jsonify_form(form)


class AccessKeyRequired(Forbidden):
    pass


class RegistrationRequired(Forbidden):
    pass
