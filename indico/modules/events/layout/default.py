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

from flask import session

from indico.modules.events.layout.util import MenuEntryData, get_menu_entry_by_name
from indico.util.i18n import _


def _visibility_my_conference(event):
    return session.user and (get_menu_entry_by_name('my_contributions', event).is_visible or
                             get_menu_entry_by_name('my_sessions', event).is_visible)


def get_default_menu_entries():
    return [
        MenuEntryData(
            title=_("Overview"),
            name='overview',
            endpoint='events.display_overview',
            position=0,
            static_site=True
        ),
        MenuEntryData(
            title=_("My Conference"),
            name='my_conference',
            endpoint='event.myconference',
            position=7,
            visible=_visibility_my_conference
        )
    ]
