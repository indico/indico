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

from indico.core import signals
from indico.modules.admin.controllers.base import RHAdminBase
from indico.util.i18n import _
from indico.web.menu import SideMenuSection


__all__ = ('RHAdminBase',)


@signals.menu.sections.connect_via('admin-sidemenu')
def _sidemenu_sections(sender, **kwargs):
    yield SideMenuSection('security', _("Security"), 90, icon='shield')
    yield SideMenuSection('user_management', _("User Management"), 60, icon='users')
    yield SideMenuSection('customization', _("Customization"), 50, icon='wrench')
    yield SideMenuSection('integration', _("Integration"), 30, icon='earth')
    yield SideMenuSection('homepage', _("Homepage"), 40, icon='home')
