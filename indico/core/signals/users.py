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

from blinker import Namespace

_signals = Namespace()


profile_sidemenu = _signals.signal('profile-sidemenu', """
Expected to return `MenuItem` instances to be added to the user profile side menu.
The *sender* is the user whose profile is currently being displayed.
""")

preferences = _signals.signal('preferences', """
Expected to return a `ExtraUserPreferences` subclass which implements extra
preferences for the user preference page. The *sender* is the user for whom the
preferences page is being shown which might not be the currently logged-in
user!
""")
