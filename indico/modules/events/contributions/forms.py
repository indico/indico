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

from datetime import timedelta

from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import StringField, TextAreaField
from wtforms.validators import DataRequired

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.events.contributions.fields import ContributionPersonListField
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import TimeDeltaField, PrincipalListField, IndicoEnumRadioField, IndicoLocationField
from indico.web.forms.validators import UsedIf
from indico.util.i18n import _


class ContributionForm(IndicoForm):
    title = StringField(_("Title"), [DataRequired()])
    description = TextAreaField(_("Description"))
    duration = TimeDeltaField(_("Duration"), [DataRequired()], default=timedelta(minutes=20),
                              units=('minutes', 'hours'),
                              description=_("The duration of the contribution"))
    type = QuerySelectField(_("Type"), get_label='name', allow_blank=True, blank_text=_("No type selected"))
    person_link_data = ContributionPersonListField(_("People"), allow_authors=True)
    location_data = IndicoLocationField(_("Location"),
                                        description=_("The physical location where the contribution takes place."))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(ContributionForm, self).__init__(*args, **kwargs)
        self.type.query = self.event.contribution_types


class ContributionProtectionForm(IndicoForm):
    protection_mode = IndicoEnumRadioField(_('Protection mode'), enum=ProtectionMode)
    acl = PrincipalListField(_('Access control list'), [UsedIf(lambda form, field: form.contrib.is_protected)],
                             serializable=False, groups=True,
                             description=_('List of users allowed to access the contribution. If the protection mode '
                                           'is set to inheriting, these users have access in addition to the users '
                                           'who can access the parent object.'))
    managers = PrincipalListField(_('Managers'), description=_('List of users allowed to modify the contribution'),
                                  serializable=False, groups=True)
    submitters = PrincipalListField(_('Submitters'), serializable=False, groups=True,
                                    description=_('List of users allowed to submit materials for this contribution'))

    def __init__(self, *args, **kwargs):
        self.contrib = kwargs.pop('contrib')
        super(ContributionProtectionForm, self).__init__(*args, **kwargs)
