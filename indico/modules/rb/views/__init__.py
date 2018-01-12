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

from flask import render_template_string

from indico.util.i18n import _
from indico.util.string import to_unicode
from indico.web.breadcrumbs import render_breadcrumbs
from indico.web.views import WPDecorated, WPJinjaMixin


class WPRoomBookingBase(WPJinjaMixin, WPDecorated):
    template_prefix = 'rb/'
    title = _('Room Booking')

    def __init__(self, rh, **kwargs):
        kwargs['active_menu_item'] = self.sidemenu_option
        WPDecorated.__init__(self, rh, **kwargs)

    def getJSFiles(self):
        return WPDecorated.getJSFiles(self) + self._includeJSPackage(['Management', 'RoomBooking'])

    def _get_breadcrumbs(self):
        return render_breadcrumbs(_('Room Booking'))

    def _getBody(self, params):
        return self._getPageContent(params)


class WPRoomBookingLegacyBase(WPRoomBookingBase):
    def _getBody(self, params):
        # Legacy handling for pages that do not use Jinja inheritance.
        tpl = "{% extends 'rb/base.html' %}{% block content %}{{ _body | safe }}{% endblock %}"
        body = to_unicode(self._getPageContent(params))
        return render_template_string(tpl, _body=body, **self._kwargs)

    def _getPageContent(self, params):
        raise NotImplementedError
