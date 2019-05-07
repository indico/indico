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

from indico.modules.events.management.views import WPEventManagement
from indico.util.i18n import _
from indico.web.views import WPNewBase


class WPRoomBookingBase(WPNewBase):
    template_prefix = 'rb/'
    title = _('Room Booking')
    bundles = ('common.js', 'common.css', 'react.js', 'react.css', 'semantic-ui.js', 'semantic-ui.css',
               'module_rb_new.js', 'module_rb_new.css')


class WPEventBookingList(WPEventManagement):
    template_prefix = 'rb/'
    sidemenu_option = 'room_booking'
    bundles = ('module_rb_new.event.js', 'module_rb_new.css')
