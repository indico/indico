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

from indico.core import signals
from indico.modules.groups.core import GroupProxy
from indico.util.i18n import _
from indico.web.flask.util import url_for


__all__ = ('GroupProxy',)


@signals.admin_sidemenu.connect
def _extend_admin_menu(sender, **kwargs):
    from MaKaC.webinterface.wcomponents import SideMenuItem
    return 'groups', SideMenuItem(_("Groups"), url_for('groups.groups'), section='user_management')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    target.local_groups |= source.local_groups
    source.local_groups.clear()
