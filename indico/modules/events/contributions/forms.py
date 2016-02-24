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

from indico.modules.events.contributions.fields import ContributionPersonListField, SubContributionPersonListField
from indico.modules.events.contributions.models.references import ContributionReference
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (TimeDeltaField, PrincipalListField, IndicoLocationField, IndicoProtectionField,
                                     ReferencesField)
from indico.web.forms.validators import UsedIf, MaxDuration
from indico.util.i18n import _


class ContributionForm(IndicoForm):
    title = StringField(_("Title"), [DataRequired()])
    description = TextAreaField(_("Description"))
    duration = TimeDeltaField(_("Duration"), [DataRequired(), MaxDuration(timedelta(hours=24))],
                              default=timedelta(minutes=20), units=('minutes', 'hours'),
                              description=_("The duration of the contribution"))
    type = QuerySelectField(_("Type"), get_label='name', allow_blank=True, blank_text=_("No type selected"))
    person_link_data = ContributionPersonListField(_("People"), allow_authors=True)
    location_data = IndicoLocationField(_("Location"),
                                        description=_("The physical location where the contribution takes place."))
    references = ReferencesField(_("External IDs"), reference_class=ContributionReference,
                                 description=_("Manage external resources for this contribution"))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(ContributionForm, self).__init__(*args, **kwargs)
        self.type.query = self.event.contribution_types


class ContributionProtectionForm(IndicoForm):
    protection_mode = IndicoProtectionField(_('Protection mode'))
    acl = PrincipalListField(_('Access control list'), [UsedIf(lambda form, field: form.protected_object.is_protected)],
                             serializable=False, groups=True,
                             description=_('List of users allowed to access the contribution. If the protection mode '
                                           'is set to inheriting, these users have access in addition to the users '
                                           'who can access the parent object.'))
    managers = PrincipalListField(_('Managers'), serializable=False, groups=True,
                                  description=_('List of users allowed to modify the contribution'))
    submitters = PrincipalListField(_('Submitters'), serializable=False, groups=True,
                                    description=_('List of users allowed to submit materials for this contribution'))

    def __init__(self, *args, **kwargs):
        self.protected_object = kwargs.pop('contrib')
        super(ContributionProtectionForm, self).__init__(*args, **kwargs)


class SubContributionForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()])
    description = TextAreaField(_('Description'))
    duration = TimeDeltaField(_('Duration'), [DataRequired(), MaxDuration(timedelta(hours=24))],
                              default=timedelta(minutes=20), units=('minutes', 'hours'),
                              description=_('The duration of the subcontribution'))
    speakers = SubContributionPersonListField(_('Speakers'), description=_('List of the subcontributions speakers'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(SubContributionForm, self).__init__(*args, **kwargs)
