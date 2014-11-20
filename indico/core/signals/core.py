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


after_process = _signals.signal('after-process', """
Called after an Indico request has been processed.
""")

before_retry = _signals.signal('before-retry', """
Called before an Indico request is being retried.
""")

indico_help = _signals.signal('indico-help', """
Expected to return a dict containing entries for the *Indico help* page::

    entries = {
        _('Section title'): {
            _('Item title'): ('ihelp/.../item.html', 'ihelp/.../item.pdf'),
            _('Item title 2'): ('ihelp/.../item2.html', 'ihelp/.../item2.pdf')
        }
    }
""")

user_preferences = _signals.signal('user-preferences', """
Expected to return/yield one or more ``(title, content)`` tuples which are
shown on the "User Preferences" page. The *sender* is the user for whom the
preferences page is being shown which might not be the currently logged-in
user!
""")
