# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.management.views import WPEventManagement
from indico.util.i18n import _
from indico.web.views import WPNewBase


class WPRoomBookingBase(WPNewBase):
    template_prefix = 'rb/'
    title = _('Room Booking')
    bundles = ('common.js', 'common.css', 'react.js', 'react.css', 'semantic-ui.js', 'semantic-ui.css',
               'module_rb.js', 'module_rb.css')


class WPEventBookingList(WPEventManagement):
    template_prefix = 'rb/'
    sidemenu_option = 'room_booking'
    bundles = ('module_rb.event.js', 'module_rb.css')
