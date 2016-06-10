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

from operator import itemgetter

from wtforms import BooleanField, StringField

from indico.modules.events.sessions import COORDINATOR_PRIV_TITLES, COORDINATOR_PRIV_DESCS
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (AccessControlListField, IndicoProtectionField, PrincipalListField,
                                     IndicoPasswordField)
from indico.web.forms.widgets import SwitchWidget
from indico.web.forms.validators import UsedIf


class EventProtectionForm(IndicoForm):
    protection_mode = IndicoProtectionField(_('Protection mode'), protected_object=lambda form: form.protected_object)
    acl = AccessControlListField(_('Access control list'),
                                 [UsedIf(lambda form, field: form.protected_object.is_protected)],
                                 groups=True, allow_emails=True, allow_networks=True, allow_external=True)
    access_key = IndicoPasswordField(_('Access key'), [UsedIf(lambda form, field: form.protected_object.is_protected)],
                                     toggle=True, classes=['event-protection-access-key'],
                                     description=_('It is more secure to use only the ACL and not set an access key. '
                                                   '<b>It will have no effect if the event is not protected</b>'))
    no_access_contact = StringField(_('No access contact'),
                                    [UsedIf(lambda form, field: form.protected_object.is_protected)],
                                    description=_('Contact in case of no access. <b>Used only if the '
                                                  'event is protected</b>'))
    managers = PrincipalListField(_('Managers'), groups=True, allow_emails=True, allow_external=True,
                                  description=_('List of users allowed to modify the event'))
    submitters = PrincipalListField(_('Submitters', allow_emails=True), allow_external=True,
                                    description=_('List of users with submission rights'))
    priv_fields = set()

    def __init__(self, *args, **kwargs):
        self.protected_object = kwargs.pop('event')
        super(EventProtectionForm, self).__init__(*args, **kwargs)

    @classmethod
    def _create_coordinator_priv_fields(cls):
        for name, title in sorted(COORDINATOR_PRIV_TITLES.iteritems(), key=itemgetter(1)):
            setattr(cls, name, BooleanField(title, widget=SwitchWidget(), description=COORDINATOR_PRIV_DESCS[name]))
            cls.priv_fields.add(name)


EventProtectionForm._create_coordinator_priv_fields()
