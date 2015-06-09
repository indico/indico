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
from indico.core.settings import SettingsProxy
from indico.util.i18n import _
from indico.web.flask.util import url_for
from MaKaC.webinterface.wcomponents import SideMenuItem


__all__ = ('settings',)


settings = SettingsProxy('cephalopod', {
    'tracked': False,
    'contact_email': None,
    'contact_name': None,
    'uuid': None
})


@signals.admin_sidemenu.connect
def _extend_admin_menu(sender, **kwargs):
    return 'cephalopod', SideMenuItem(_("Instance Tracking"), url_for('cephalopod.index'))
