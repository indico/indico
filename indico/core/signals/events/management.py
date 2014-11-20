# This file is part of Indico.
# Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

from indico.core.signals import _signals


event_management_sidemenu = _signals.signal('event-management-sidemenu', """
Expected to return `(plugin_menu_item_name, SideMenuItem)` tuples to be added to
the event management side menu. The *sender* is the event object.
""")

event_management_clone = _signals.signal('event-management-clone', """
Expected to return an instance of a ``EventCloner`` subclass implementing
the cloning behavior. The *sender* is the event object.
""")

event_management_url = _signals.signal('event-management-url', """
Expected to return a URL for the event management page of the plugin.
This is used when someone who does not have event management access wants
to go to the event management area. He is then redirected to one of the URLs
returned by plugins, i.e. it is not guaranteed that the user ends up on a
specific plugin's management page. The signal should return None if the current
user (available via ``session.user``) cannot access the management area.
The *sender* is the event object.
""")
