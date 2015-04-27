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

from blinker import Namespace

_signals = Namespace()


app_created = _signals.signal('app-created', """
Called when the app has been created. The *sender* is the flask app.
""")

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

indico_menu = _signals.signal('indico-menu', """
Expected to return `HeaderMenuEntry` objects which are then added to the
Indico head menu.
""")

admin_sidemenu = _signals.signal('admin-sidemenu', """
Expected to return `(extra_menu_item_name, SideMenuItem)` tuples to be added to
the admin side menu.
""")

merge_users = _signals.signal('merge-users', """
Called when two users are merged. The *sender* is the main user while the merged
user (i.e. the one being deleted in the merge) is passed via the *merged* kwarg.
""")
