# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, redirect, request, session
from werkzeug.exceptions import Forbidden, NotFound

from indico.modules.events import Event
from indico.modules.events.registration.util import get_event_regforms_registrations
from indico.modules.events.views import WPAccessKey
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.rh import RH


class RHEventBase(RH):
    def _process_args(self):
        self.event = Event.get(int(request.view_args['confId']))
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

            msg = [_("You are not authorized to access this event.")]
            if self.event.no_access_contact:
                msg.append(_("If you believe you should have access, please contact {}")
                           .format(self.event.no_access_contact))
            raise Forbidden(' '.join(msg))

    def _show_access_key_form(self):
        return WPAccessKey.render_template('display/access_key.html', event=self.event)

    def _show_registration_form(self):
        displayed_regforms, user_registrations = get_event_regforms_registrations(self.event, session.user)
        if len(displayed_regforms) == 1:
            return redirect(url_for('event_registration.display_regform', displayed_regforms[0]))
        return redirect(url_for('event_registration.display_regform_list', self.event))

    def _do_process(self):
        try:
            return RHEventBase._do_process(self)
        except AccessKeyRequired:
            return self._show_access_key_form()
        except RegistrationRequired:
            if request.is_xhr:
                raise
            return self._show_registration_form()


class AccessKeyRequired(Forbidden):
    pass


class RegistrationRequired(Forbidden):
    pass
