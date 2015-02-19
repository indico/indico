# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import render_template

from indico.modules.vc.models.vc_rooms import VCRoomEventAssociation
from indico.modules.vc.plugins import VCPluginMixin
from indico.modules.vc.forms import VCPluginSettingsFormBase
from indico.web.flask.templating import template_hook

__all__ = ('VCPluginMixin', 'VCPluginSettingsFormBase')


@template_hook('event-header')
def _inject_event_header(event, **kwargs):
    event_vc_rooms = VCRoomEventAssociation.find_for_event(event).all()
    return render_template('vc/event_header.html', event=event, event_vc_rooms=event_vc_rooms)
