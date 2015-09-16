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

from indico.core import signals
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuSection, SideMenuItem


@signals.menu.sections.connect_via('admin-sidemenu')
def _sidemenu_sections(sender, **kwargs):
    yield 'security', SideMenuSection(_("Security"), 90, icon='shield')
    yield 'user_management', SideMenuSection(_("User Management"), 60, icon='users')
    yield 'customization', SideMenuSection(_("Customization"), 50, icon='wrench')
    yield 'integration', SideMenuSection(_("Integration"), 40, icon='earth')


@signals.menu.items.connect_via('admin-sidemenu')
def _sidemenu_items(sender, **kwargs):
    yield 'general', SideMenuItem(_('General Settings'), url_for('admin.adminList'), 100, icon='settings')
    yield 'storage', SideMenuItem(_('Disk Storage'), url_for('admin.adminSystem'), 70, icon='stack')
    yield 'ip_domains', SideMenuItem(_('IP Domains'), url_for('admin.domainList'), section='security')
    yield 'ip_acl', SideMenuItem(_('IP-based ACL'), url_for('admin.adminServices-ipbasedacl'), section='security')
    yield 'layout', SideMenuItem(_('Layout'), url_for('admin.adminLayout'), section='customization')
    yield 'homepage', SideMenuItem(_('Homepage'), url_for('admin.updateNews'), section='customization')
    yield 'protection', SideMenuItem(_('Protection'), url_for('admin.adminProtection'), section='security')
