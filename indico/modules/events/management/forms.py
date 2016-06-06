# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import AccessControlListField, IndicoProtectionField
from indico.web.forms.validators import UsedIf


class EventProtectionForm(IndicoForm):
    protection_mode = IndicoProtectionField(_('Protection mode'), protected_object=lambda form: form.protected_object)
    acl = AccessControlListField(_('Access control list'),
                                 [UsedIf(lambda form, field: form.protected_object.is_protected)],
                                 groups=True, allow_emails=True, allow_networks=True,
                                 description=_('List of users allowed to access the event.'))

    def __init__(self, *args, **kwargs):
        self.protected_object = kwargs.pop('event')
        super(EventProtectionForm, self).__init__(*args, **kwargs)
