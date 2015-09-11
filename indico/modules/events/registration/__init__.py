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
from indico.core.roles import ManagementRole
from indico.modules.events import Event
from indico.util.i18n import _


@signals.acl.get_management_roles.connect_via(Event)
def _get_management_roles(sender, **kwargs):
    return RegistrationRole


class RegistrationRole(ManagementRole):
    name = 'registration'
    friendly_name = _('Registration')
    description = _('Grants management access to the registration form..')


# TODO: In the new registration module, being able to manage forms and
# being able to see registrants should probably use different roles.  That
# way you can hand out read access to the full registrant list without the
# risk of someone changing data or the form itself.
