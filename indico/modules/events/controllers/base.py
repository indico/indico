# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, request, session
from werkzeug.exceptions import Forbidden, NotFound

from indico.modules.events import Event
from indico.modules.events.views import WPAccessKey
from indico.util.i18n import _
from indico.web.rh import RH


class RHEventBase(RH):
    def _process_args(self):
        self.event = Event.get(int(request.view_args['confId']))
        if self.event is None:
            raise NotFound(_('An event with this ID does not exist.'))
        elif self.event.is_deleted:
            raise NotFound(_('This event has been deleted.'))


class RHDisplayEventBase(RHEventBase):
    def _forbidden_if_not_admin(self):
        if not request.is_xhr and session.user and session.user.is_admin:
            flash(_('This page is currently not visible by non-admin users (menu entry disabled)!'), 'warning')
        else:
            raise Forbidden

    def _check_access(self):
        if self.event.can_access(session.user):
            return
        elif self.event.access_key:
            raise AccessKeyRequired
        elif session.user is None:
            raise Forbidden
        else:
            msg = [_("You are not authorized to access this event.")]
            if self.event.no_access_contact:
                msg.append(_("If you believe you should have access, please contact {}")
                           .format(self.event.no_access_contact))
            raise Forbidden(' '.join(msg))

    def _show_access_key_form(self):
        return WPAccessKey.render_template('display/access_key.html', event=self.event)

    def _do_process(self):
        try:
            return RHEventBase._do_process(self)
        except AccessKeyRequired:
            return self._show_access_key_form()


class AccessKeyRequired(Forbidden):
    pass
