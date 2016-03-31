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
from wtforms.validators import DataRequired, ValidationError

from indico.modules.events.contributions.fields import ContributionPersonLinkListField, SubContributionPersonLinkListField
from indico.modules.events.contributions.models.references import ContributionReference, SubContributionReference
from indico.modules.events.fields import ReferencesField
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (TimeDeltaField, PrincipalListField, IndicoProtectionField, IndicoLocationField,
                                     IndicoDateTimeField)
from indico.web.forms.validators import UsedIf, DateTimeRange, MaxDuration
from indico.util.i18n import _


class ContributionForm(IndicoForm):
    title = StringField(_("Title"), [DataRequired()])
    description = TextAreaField(_("Description"))
    start_date = IndicoDateTimeField(_("Start date"), [DataRequired(),
                                                       DateTimeRange(earliest=lambda form, field: form.event.start_dt,
                                                                     latest=lambda form, field: form.event.end_dt)],
                                     description=_("Start date of the contribution"))
    duration = TimeDeltaField(_("Duration"), [DataRequired(), MaxDuration(timedelta(hours=24))],
                              default=timedelta(minutes=20), units=('minutes', 'hours'),
                              description=_("The duration of the contribution"))
    type = QuerySelectField(_("Type"), get_label='name', allow_blank=True, blank_text=_("No type selected"))
    person_link_data = ContributionPersonLinkListField(_("People"), allow_authors=True)
    location_data = IndicoLocationField(_("Location"),
                                        description=_("The physical location where the contribution takes place."))
    references = ReferencesField(_("External IDs"), reference_class=ContributionReference,
                                 description=_("Manage external resources for this contribution"))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.contrib = kwargs.pop('contrib', None)
        self.timezone = self.event.timezone
        super(ContributionForm, self).__init__(*args, **kwargs)
        self.type.query = self.event.contribution_types
        if self.contrib is None or not self.contrib.is_scheduled:
            del self.start_date

    def validate_duration(self, field):
        start_date_field = self.start_date
        if start_date_field and start_date_field.data and start_date_field.data + field.data > self.event.end_dt:
            raise ValidationError(_('With the current duration the contribution exceeds the event end date'))

    def get_custom_field_names(self):
        return tuple([field_name for field_name in self._fields.iterkeys() if field_name.startswith('custom_')])


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
    speakers = SubContributionPersonLinkListField(_('Speakers'), allow_submitters=False,
                                                  description=_('The speakers of the subcontribution'))
    references = ReferencesField(_("External IDs"), reference_class=SubContributionReference,
                                 description=_("Manage external resources for this sub-contribution"))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.subcontrib = kwargs.pop('subcontrib', None)
        super(SubContributionForm, self).__init__(*args, **kwargs)


class ContributionStartDateForm(IndicoForm):
    start_dt = IndicoDateTimeField(_('Start date'), [DataRequired(),
                                                     DateTimeRange(earliest=lambda form, field: form.event.start_dt,
                                                                   latest=lambda form, field: form.event.end_dt)],
                                   allow_clear=False)

    def __init__(self, *args, **kwargs):
        self.contrib = kwargs.pop('contrib')
        self.event = self.contrib.event_new
        self.timezone = self.event.timezone
        super(ContributionStartDateForm, self).__init__(*args, **kwargs)

    def validate_start_dt(self, field):
        if field.data + self.contrib.duration > self.event.end_dt:
            raise ValidationError(_('The selected date is incorrect, since the overall time of this contribution would'
                                    'exceed the event end date. Either change the date or the contribution duration'))


class ContributionDurationForm(IndicoForm):
    duration = TimeDeltaField(_('Duration'), [DataRequired(), MaxDuration(timedelta(days=1))],
                              default=timedelta(minutes=20), units=('minutes', 'hours'),
                              description=_('The duration of the contribution'))

    def __init__(self, *args, **kwargs):
        self.contrib = kwargs.pop('contrib')
        super(ContributionDurationForm, self).__init__(*args, **kwargs)

    def validate_duration(self, field):
        if field.errors:
            return
        if self.contrib.is_scheduled and self.contrib.start_dt + field.data > self.contrib.event_new.end_dt:
            raise ValidationError(_('With the current value, the contribution would exceed event end date'))
