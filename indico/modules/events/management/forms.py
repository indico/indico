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

import re
from datetime import timedelta, datetime
from operator import itemgetter, attrgetter

from flask import request, session
from markupsafe import escape
from pytz import timezone
from werkzeug.datastructures import ImmutableMultiDict
from wtforms import BooleanField, StringField, FloatField, SelectField, TextAreaField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import InputRequired, DataRequired, ValidationError, Optional, NumberRange

from indico.core.config import Config
from indico.core.db import db
from indico.modules.categories import Category
from indico.modules.categories.fields import CategoryField
from indico.modules.categories.util import get_visibility_options
from indico.modules.designer import PageSize
from indico.modules.designer.util import get_inherited_templates
from indico.modules.events import Event, LegacyEventMapping
from indico.modules.events.cloning import EventCloner
from indico.modules.events.fields import EventPersonLinkListField, ReferencesField
from indico.modules.events.models.events import EventType
from indico.modules.events.models.references import EventReference
from indico.modules.events.sessions import COORDINATOR_PRIV_TITLES, COORDINATOR_PRIV_DESCS
from indico.modules.events.timetable.util import get_top_level_entries
from indico.util.date_time import format_human_timedelta, now_utc, relativedelta
from indico.util.i18n import _
from indico.util.string import is_valid_mail
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (AccessControlListField, IndicoProtectionField, PrincipalListField,
                                     IndicoEnumSelectField, IndicoPasswordField, IndicoDateTimeField,
                                     IndicoTimezoneSelectField, IndicoLocationField, MultiStringField,
                                     IndicoTagListField, IndicoRadioField, RelativeDeltaField, IndicoDateField,
                                     IndicoSelectMultipleCheckboxField, IndicoWeekDayRepetitionField)
from indico.web.forms.validators import LinkedDateTime, HiddenUnless
from indico.web.forms.widgets import SwitchWidget, CKEditorWidget


CLONE_REPEAT_CHOICES = (
    ('once', _('Clone Once')),
    ('interval', _('Clone with fixed Interval')),
    ('pattern', _('Clone with recurring Pattern'))
)


class EventDataForm(IndicoForm):
    title = StringField(_('Event title'), [DataRequired()])
    description = TextAreaField(_('Description'), widget=CKEditorWidget(simple=True, images=True, height=250))
    url_shortcut = StringField(_('URL shortcut'), filters=[lambda x: (x or None)])

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(EventDataForm, self).__init__(*args, **kwargs)
        # TODO: Add a custom widget showing the prefix right before the field
        prefix = '{}/e/'.format(Config.getInstance().getBaseURL())
        self.url_shortcut.description = _('<strong>{}SHORTCUT</strong> - the URL shortcut must be unique within '
                                          'this Indico instance and is not case sensitive.').format(prefix)

    def validate_url_shortcut(self, field):
        shortcut = field.data
        if not shortcut:
            return
        if shortcut.isdigit():
            raise ValidationError(_("The URL shortcut must contain at least one character that is not a digit."))
        if not re.match(r'^[a-zA-Z0-9/._-]+$', shortcut):
            raise ValidationError(_("The URL shortcut contains an invalid character."))
        if '//' in shortcut:
            raise ValidationError(_("The URL shortcut may not contain two consecutive slashes."))
        if shortcut[0] == '/' or shortcut[-1] == '/':
            raise ValidationError(_("The URL shortcut may not begin/end with a slash."))
        conflict = (Event.query
                    .filter(db.func.lower(Event.url_shortcut) == shortcut.lower(),
                            ~Event.is_deleted,
                            Event.id != self.event.id)
                    .has_rows())
        if conflict:
            raise ValidationError(_("The URL shortcut is already used in another event."))
        if LegacyEventMapping.query.filter_by(legacy_event_id=shortcut).has_rows():
            # Reject existing event ids. It'd be EXTREMELY confusing and broken to allow such a shorturl
            # Non-legacy event IDs are already covered by the `isdigit` check above.
            raise ValidationError(_("This URL shortcut is not available.") % shortcut)


class EventDatesForm(IndicoForm):
    _main_fields = ('start_dt', 'end_dt', 'timezone', 'update_timetable')
    _override_date_fields = ('start_dt_override', 'end_dt_override')

    timezone = IndicoTimezoneSelectField(_('Timezone'), [DataRequired()])
    start_dt = IndicoDateTimeField(_("Start"), [DataRequired()], allow_clear=False)
    end_dt = IndicoDateTimeField(_("End"), [DataRequired(), LinkedDateTime('start_dt', not_equal=True)],
                                 allow_clear=False)
    update_timetable = BooleanField(_('Update timetable'), widget=SwitchWidget(),
                                    description=_("Move sessions/contributions/breaks in the timetable according "
                                                  "to the new event start time."))
    start_dt_override = IndicoDateTimeField(_("Start"), [Optional()], allow_clear=True,
                                            description=_("Specifying this date overrides the start date displayed "
                                                          "on the main conference page."))
    end_dt_override = IndicoDateTimeField(_("End"), [Optional(), LinkedDateTime('start_dt_override', not_equal=True)],
                                          allow_clear=True,
                                          description=_("Specifying this date overrides the end date displayed "
                                                        "on the main conference page."))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(EventDatesForm, self).__init__(*args, **kwargs)
        # timetable synchronization
        self.check_timetable_boundaries = (self.event.type_ != EventType.lecture)
        if self.check_timetable_boundaries:
            self.toplevel_timetable_entries = get_top_level_entries(self.event)
            if not self.toplevel_timetable_entries:
                self.check_timetable_boundaries = False
        if not self.check_timetable_boundaries:
            del self.update_timetable
        # displayed dates
        self.has_displayed_dates = (self.event.type_ == EventType.conference)
        if self.has_displayed_dates:
            self.start_dt_override.default_time = self.start_dt.data.astimezone(timezone(self.timezone.data)).time()
            self.end_dt_override.default_time = self.end_dt.data.astimezone(timezone(self.timezone.data)).time()
        else:
            del self.start_dt_override
            del self.end_dt_override

    def validate_start_dt(self, field):
        if not self.check_timetable_boundaries or self.update_timetable.data or field.object_data == field.data:
            return
        if field.data > min(self.toplevel_timetable_entries, key=attrgetter('start_dt')).start_dt:
            raise ValidationError(_("To use this start date the timetable must be updated."))

    def validate_end_dt(self, field):
        if not self.check_timetable_boundaries:
            return
        start_dt_offset = self.start_dt.data - self.start_dt.object_data
        end_buffer = field.data - max(self.toplevel_timetable_entries, key=attrgetter('end_dt')).end_dt
        delta = max(timedelta(), start_dt_offset - end_buffer)
        if delta:
            delta_str = format_human_timedelta(delta, 'minutes', True)
            raise ValidationError(_("The event is too short to fit all timetable entries. "
                                    "It must be at least {} longer.").format(delta_str))


class EventLocationForm(IndicoForm):
    location_data = IndicoLocationField(_('Location'), allow_location_inheritance=False)


class EventPersonsForm(IndicoForm):
    person_link_data = EventPersonLinkListField(_('Chairpersons'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(EventPersonsForm, self).__init__(*args, **kwargs)
        if self.event.type_ == EventType.lecture:
            self.person_link_data.label.text = _('Speakers')


class EventContactInfoForm(IndicoForm):
    _contact_fields = ('contact_title', 'contact_emails', 'contact_phones')

    contact_title = StringField(_('Title'), [DataRequired()])
    contact_emails = MultiStringField(_('Emails'), field=('email', _('email')), unique=True, flat=True, sortable=True)
    contact_phones = MultiStringField(_('Phone numbers'), field=('phone', _('number')), unique=True, flat=True,
                                      sortable=True)
    organizer_info = TextAreaField(_('Organizers'))
    additional_info = TextAreaField(_('Additional information'),
                                    widget=CKEditorWidget(simple=True, images=True, height=250),
                                    description=_("This text is displayed on the main conference page."))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(EventContactInfoForm, self).__init__(*args, **kwargs)
        if self.event.type_ != EventType.lecture:
            del self.organizer_info
        if self.event.type_ != EventType.conference:
            del self.additional_info

    def validate_contact_emails(self, field):
        for email in field.data:
            if not is_valid_mail(email, False):
                raise ValidationError(_('Invalid email address: {}').format(escape(email)))


class EventClassificationForm(IndicoForm):
    keywords = IndicoTagListField(_('Keywords'))
    references = ReferencesField(_('External IDs'), reference_class=EventReference)

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super(EventClassificationForm, self).__init__(*args, **kwargs)
        if event.type_ != EventType.meeting:
            del self.references


class EventProtectionForm(IndicoForm):
    protection_mode = IndicoProtectionField(_('Protection mode'),
                                            protected_object=lambda form: form.protected_object,
                                            acl_message_url=lambda form: url_for('event_management.acl_message',
                                                                                 form.protected_object))
    acl = AccessControlListField(_('Access control list'), groups=True, allow_emails=True, allow_networks=True,
                                 allow_external=True, default_text=_('Restrict access to this event'),
                                 description=_('List of users allowed to access the event.'))
    access_key = IndicoPasswordField(_('Access key'), toggle=True,
                                     description=_('It is more secure to use only the ACL and not set an access key. '
                                                   '<strong>It will have no effect if the event is not '
                                                   'protected</strong>'))
    own_no_access_contact = StringField(_('No access contact'),
                                        description=_('Contact information shown when someone lacks access to the '
                                                      'event'))
    managers = PrincipalListField(_('Managers'), groups=True, allow_emails=True, allow_external=True,
                                  description=_('List of users allowed to modify the event'))
    submitters = PrincipalListField(_('Submitters'), groups=True, allow_emails=True, allow_external=True,
                                    description=_('List of users with submission rights'))
    visibility = SelectField(_("Visibility"), [Optional()], coerce=lambda x: None if x == '' else int(x),
                             description=_("""From which point in the category tree this event will be visible from """
                                           """(number of categories upwards). Applies to "Today's events" and """
                                           """Calendar only. If the event is moved, this number will be preserved."""))
    priv_fields = set()

    def __init__(self, *args, **kwargs):
        self.protected_object = event = kwargs.pop('event')
        super(EventProtectionForm, self).__init__(*args, **kwargs)
        self._init_visibility(event)

    def _get_event_own_visibility_horizon(self, event):
        if self.visibility.data is None:  # unlimited
            return Category.get_root()
        elif self.visibility.data == 0:  # invisible
            return None
        else:
            return event.category.nth_parent(self.visibility.data - 1)

    def _init_visibility(self, event):
        self.visibility.choices = get_visibility_options(event, allow_invisible=True)
        # Check if event visibility would be affected by any of the categories
        real_horizon = event.category.real_visibility_horizon
        own_horizon = self._get_event_own_visibility_horizon(event)
        if own_horizon and real_horizon and real_horizon.is_descendant_of(own_horizon):
            self.visibility.warning = _("This event's visibility is currently limited by that of '{}'.").format(
                real_horizon.title)

    @classmethod
    def _create_coordinator_priv_fields(cls):
        for name, title in sorted(COORDINATOR_PRIV_TITLES.iteritems(), key=itemgetter(1)):
            setattr(cls, name, BooleanField(title, widget=SwitchWidget(), description=COORDINATOR_PRIV_DESCS[name]))
            cls.priv_fields.add(name)


EventProtectionForm._create_coordinator_priv_fields()


class PosterPrintingForm(IndicoForm):
    template = SelectField(_('Template'))
    margin_horizontal = FloatField(_('Horizontal margins'), [InputRequired()], default=0)
    margin_vertical = FloatField(_('Vertical margins'), [InputRequired()], default=0)
    page_size = IndicoEnumSelectField(_('Page size'), enum=PageSize, default=PageSize.A4)

    def __init__(self, event, **kwargs):
        all_templates = set(event.designer_templates) | get_inherited_templates(event)
        poster_templates = [tpl for tpl in all_templates if tpl.type.name == 'poster']
        super(PosterPrintingForm, self).__init__(**kwargs)
        self.template.choices = sorted(((unicode(tpl.id), tpl.title) for tpl in poster_templates), key=itemgetter(1))


class CloneRepeatabilityForm(IndicoForm):
    repeatability = IndicoRadioField(_('How to repeat'), choices=CLONE_REPEAT_CHOICES, coerce=lambda x: x or None)


class CloneContentsForm(CloneRepeatabilityForm):
    selected_items = IndicoSelectMultipleCheckboxField(_('What to clone'))

    def __init__(self, event, set_defaults=False, **kwargs):
        options = EventCloner.get_cloners(event)
        visible_options = filter(attrgetter('is_visible'), options)
        default_selected_items = kwargs.get('selected_items', [option.name for option in options if option.is_default])

        if set_defaults:
            default_category = kwargs['category']['id'] if 'category' in kwargs else None
            form_params = {
                'repeatability': request.form.get('repeatability', kwargs.pop('repeatability', None)),
                'selected_items': (request.form.getlist('selected_items') or default_selected_items),
                'category': request.form.get('category', default_category),
                'csrf_token': request.form.get('csrf_token')
            }
            kwargs['formdata'] = ImmutableMultiDict(form_params)

        super(CloneContentsForm, self).__init__(**kwargs)
        self.selected_items.choices = [(option.name, option.friendly_name) for option in visible_options]
        self.selected_items.disabled_choices = [option.name for option in visible_options if not option.is_available]


class CloneCategorySelectForm(CloneContentsForm):
    category = CategoryField(_('Category'), require_event_creation_rights=True, allow_subcats=False)

    def validate_category(self, field):
        if not field.data:
            raise ValidationError(_("You have to select a category"))
        elif not field.data.can_create_events(session.user):
            raise ValidationError(_("You can't create events in this category"))


class CloneRepeatFormBase(CloneCategorySelectForm):
    def _calc_start_dt(self, event):
        local_now_date = now_utc().astimezone(event.tzinfo).date()
        if event.start_dt_local.date() >= local_now_date:
            start_dt = event.start_dt_local + timedelta(days=7)
        else:
            start_dt = event.tzinfo.localize(datetime.combine(local_now_date, event.start_dt_local.time()))
        if start_dt < now_utc():
            # if the combination of 'today' with the original start time is
            # still in the past, then let's set it for tomorrow instead
            start_dt += timedelta(days=1)
        return start_dt

    def __init__(self, event, **kwargs):
        kwargs['start_dt'] = self._calc_start_dt(event)
        super(CloneRepeatFormBase, self).__init__(event, **kwargs)


class CloneRepeatOnceForm(CloneRepeatFormBase):
    start_dt = IndicoDateTimeField(_('Starting'), allow_clear=False)


class CloneRepeatUntilFormBase(CloneRepeatOnceForm):
    stop_criterion = IndicoRadioField(_('Clone'), [DataRequired()], default='num_times',
                                      choices=(('day', _('Until a given day (inclusive)')),
                                               ('num_times', _('A number of times'))))
    until_dt = IndicoDateField(_('Day'), [HiddenUnless('stop_criterion', 'day'), DataRequired()])
    num_times = IntegerField(_('Number of times'),
                             [HiddenUnless('stop_criterion', 'num_times'), DataRequired(),
                              NumberRange(1, 100, message=_("You can clone a maximum of 100 times"))],
                             default=2)

    def __init__(self, event, **kwargs):
        kwargs['until_dt'] = (self._calc_start_dt(event) + timedelta(days=14)).date()
        super(CloneRepeatUntilFormBase, self).__init__(event, **kwargs)


class CloneRepeatIntervalForm(CloneRepeatUntilFormBase):
    recurrence = RelativeDeltaField(_('Every'), [DataRequired(), NumberRange(min=1)],
                                    units=('years', 'months', 'weeks', 'days'),
                                    default=relativedelta(weeks=1))

    def validate_recurrence(self, field):
        if field.data != abs(field.data):
            raise ValidationError(_("The time period must be positive"))


class CloneRepeatPatternForm(CloneRepeatUntilFormBase):
    week_day = IndicoWeekDayRepetitionField(_('Every'))
    num_months = IntegerField(_('Months'), [DataRequired(), NumberRange(min=1)], default=1,
                              description=_("Number of months between repetitions"))
