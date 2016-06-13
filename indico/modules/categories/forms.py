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

from wtforms.fields import BooleanField, StringField

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import AccessControlListField, PrincipalListField, IndicoProtectionField, EmailListField
from indico.web.forms.widgets import SwitchWidget


class CategoryProtectionForm(IndicoForm):
    _event_creation_fields = ('event_creation_restricted', 'event_creators', 'event_creation_notification_emails')

    protection_mode = IndicoProtectionField(_('Protection mode'), protected_object=lambda form: form.protected_object)
    acl = AccessControlListField(_('Access control list'), groups=True, allow_external=True, allow_networks=True)
    managers = PrincipalListField(_('Managers'), groups=True)
    no_access_contact = StringField(_('No access contact'),
                                    description=_('Contact information shown when someone lacks access to the '
                                                  'category'))
    event_creation_restricted = BooleanField(_('Restricted event creation'), widget=SwitchWidget(),
                                             description=_('Whether the event creation should be restricted '
                                                           'to a list of specific persons'))
    event_creators = PrincipalListField(_('Event creators'), groups=True, allow_external=True,
                                        description=_('Users allowed to create events in this category'))
    event_creation_notification_emails = EmailListField(_('Event creation notification recipients'),
                                                        description=_('List of email addresses that will be '
                                                                      'notified whenever an event is created '
                                                                      'in the category'))

    def __init__(self, *args, **kwargs):
        self.protected_object = kwargs.pop('category')
        super(CategoryProtectionForm, self).__init__(*args, **kwargs)
