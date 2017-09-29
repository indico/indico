# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from flask import render_template_string

from indico.legacy.webinterface.pages.main import WPMainBase
from indico.legacy.webinterface.wcomponents import WSimpleNavigationDrawer
from indico.util.i18n import _
from indico.util.string import to_unicode


class WPRoomBookingBase(WPMainBase):
    def _getTitle(self):
        return '{} - {}'.format(WPMainBase._getTitle(self), _('Room Booking'))

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage(['Management', 'RoomBooking'])

    def _getNavigationDrawer(self):
        return WSimpleNavigationDrawer(_('Room Booking'))

    def _display(self, params):
        # TODO: when moving RB to jinja, refactor this to proper jinja inheritance
        # and only use this hack for legacy parts still using WP/W mako stuff
        tpl = "{% extends 'rb/base.html' %}{% block content %}{{ _body | safe }}{% endblock %}"
        params = dict(params, **self._kwargs)
        body = to_unicode(self._getBody(params))
        body = render_template_string(tpl, _body=body, active_menu_item=self.sidemenu_option)
        return self._applyDecoration(body)
