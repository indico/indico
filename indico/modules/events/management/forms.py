# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
from datetime import datetime, timedelta
from operator import attrgetter, itemgetter

from flask import request, session
from markupsafe import escape
from pytz import timezone
from werkzeug.datastructures import ImmutableMultiDict
from wtforms import BooleanField, EmailField, FloatField, SelectField, StringField, TextAreaField
from wtforms.fields import IntegerField, URLField
from wtforms.validators import URL, DataRequired, Email, InputRequired, NumberRange, Optional, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField

from indico.core.config import config
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
from indico.modules.events.models.labels import EventLabel
from indico.modules.events.models.references import EventReference, ReferenceType
from indico.modules.events.sessions import COORDINATOR_PRIV_DESCS, COORDINATOR_PRIV_TITLES
from indico.modules.events.timetable.util import get_top_level_entries
from indico.modules.events.util import check_permissions
from indico.util.date_time import format_datetime, format_human_timedelta, now_utc, relativedelta
from indico.util.i18n import _
from indico.util.string import validate_email
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (IndicoDateField, IndicoDateTimeField, IndicoEnumSelectField, IndicoLocationField,
                                     IndicoPasswordField, IndicoProtectionField, IndicoRadioField,
                                     IndicoSelectMultipleCheckboxField, IndicoTagListField, IndicoTimezoneSelectField,
                                     IndicoWeekDayRepetitionField, MultiStringField, RelativeDeltaField)
from indico.web.forms.fields.principals import PermissionsField
from indico.web.forms.fields.simple import IndicoLinkListField
from indico.web.forms.validators import HiddenUnless, LinkedDateTime
from indico.web.forms.widgets import CKEditorWidget, PrefixedTextWidget, SwitchWidget


CLONE_REPEAT_CHOICES = (
    ('once', _('Clone Once')),
    ('interval', _('Clone with fixed Interval')),
    ('pattern', _('Clone with recurring Pattern'))
)


class EventDataForm(IndicoForm):
    title = StringField(_('Event title'), [DataRequired()])
    description = TextAreaField(_('Description'), widget=CKEditorWidget(images=True, html_embed=True, height=250))
    url_shortcut = StringField(_('URL shortcut'), filters=[lambda x: (x or None)])

    def __init__(self, *args, event, **kwargs):
        self.event = event
        self.ckeditor_upload_url = url_for('attachments.upload_ckeditor', event)
        super().__init__(*args, **kwargs)
        prefix = f'{config.BASE_URL}/e/'
        self.url_shortcut.description = _('The URL shortcut must be unique within this Indico instance and '
                                          'is not case sensitive.').format(prefix)
        self.url_shortcut.widget = PrefixedTextWidget(prefix=prefix)

    def validate_url_shortcut(self, field):
        shortcut = field.data
        if not shortcut:
            return
        if shortcut.isdigit():
            raise ValidationError(_('The URL shortcut must contain at least one character that is not a digit.'))
        if not re.match(r'^[a-zA-Z0-9/._-]+$', shortcut):
            raise ValidationError(_('The URL shortcut contains an invalid character.'))
        if '//' in shortcut:
            raise ValidationError(_('The URL shortcut may not contain two consecutive slashes.'))
        if shortcut[0] == '/' or shortcut[-1] == '/':
            raise ValidationError(_('The URL shortcut may not begin/end with a slash.'))
        conflict = (Event.query
                    .filter(db.func.lower(Event.url_shortcut) == shortcut.lower(),
                            ~Event.is_deleted,
                            Event.id != self.event.id)
                    .has_rows())
        if conflict:
            raise ValidationError(_('The URL shortcut is already used in another event.'))
        if LegacyEventMapping.query.filter_by(legacy_event_id=shortcut).has_rows():
            # Reject existing event ids. It'd be EXTREMELY confusing and broken to allow such a shorturl
            # Non-legacy event IDs are already covered by the `isdigit` check above.
            raise ValidationError(_('This URL shortcut is not available.') % shortcut)


class EventDatesForm(IndicoForm):
    _main_fields = ('start_dt', 'end_dt', 'timezone', 'update_timetable')
    _override_date_fields = ('start_dt_override', 'end_dt_override')

    timezone = IndicoTimezoneSelectField(_('Timezone'), [DataRequired()])
    start_dt = IndicoDateTimeField(_('Start'), [InputRequired()], allow_clear=False)
    end_dt = IndicoDateTimeField(_('End'), [InputRequired(), LinkedDateTime('start_dt', not_equal=True)],
                                 allow_clear=False)
    update_timetable = BooleanField(_('Update timetable'), widget=SwitchWidget(),
                                    description=_('Move sessions/contributions/breaks in the timetable according '
                                                  'to the new event start time.'))
    start_dt_override = IndicoDateTimeField(_('Start'), [Optional()], allow_clear=True,
                                            description=_('Specifying this date overrides the start date displayed '
                                                          'on the main conference page.'))
    end_dt_override = IndicoDateTimeField(_('End'), [Optional(), LinkedDateTime('start_dt_override', not_equal=True)],
                                          allow_clear=True,
                                          description=_('Specifying this date overrides the end date displayed '
                                                        'on the main conference page.'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)
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
            start_dt = self.start_dt.data or self.start_dt.object_data
            end_dt = self.end_dt.data or self.end_dt.object_data
            self.start_dt_override.default_time = start_dt.astimezone(timezone(self.timezone.data)).time()
            self.end_dt_override.default_time = end_dt.astimezone(timezone(self.timezone.data)).time()
        else:
            del self.start_dt_override
            del self.end_dt_override

    def validate_start_dt(self, field):
        if not self.check_timetable_boundaries or self.update_timetable.data or field.object_data == field.data:
            return
        if field.data > min(self.toplevel_timetable_entries, key=attrgetter('start_dt')).start_dt:
            raise ValidationError(_('To use this start date the timetable must be updated.'))

    def validate_end_dt(self, field):
        if not self.check_timetable_boundaries:
            return
        if self.update_timetable.data:
            # if we move timetable entries according to the start date
            # change, check that there's enough time at the end.
            start_dt_offset = self.start_dt.data - self.start_dt.object_data
            end_buffer = field.data - max(self.toplevel_timetable_entries, key=attrgetter('end_dt')).end_dt
            delta = max(timedelta(), start_dt_offset - end_buffer)
            if delta:
                delta_str = format_human_timedelta(delta, 'minutes', True)
                raise ValidationError(_('The event is too short to fit all timetable entries. '
                                        'It must be at least {} longer.').format(delta_str))
        else:
            # if we do not update timetable entries, only check that
            # the event does not end before its last timetable entry;
            # a similar check for the start time is done above in that
            # field's validation method.
            max_end_dt = max(self.toplevel_timetable_entries, key=attrgetter('end_dt')).end_dt
            if field.data < max_end_dt:
                raise ValidationError(_('The event cannot end before its last timetable entry, which is at {}.')
                                      .format(format_datetime(max_end_dt, timezone=self.event.tzinfo)))


class EventLocationForm(IndicoForm):
    location_data = IndicoLocationField(_('Location'), allow_location_inheritance=False)
    own_map_url = URLField(_('Map URL'), [Optional(), URL()])

    def __init__(self, *args, **kwargs):
        event = kwargs['event']
        super().__init__(*args, **kwargs)
        if event.room:
            self.own_map_url.render_kw = {'placeholder': event.room.map_url}


class EventPersonsForm(IndicoForm):
    person_link_data = EventPersonLinkListField(_('Chairpersons'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)
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
                                    widget=CKEditorWidget(images=True, height=250),
                                    description=_('This text is displayed on the main conference page.'))

    def __init__(self, *args, event, **kwargs):
        self.event = event
        self.ckeditor_upload_url = url_for('attachments.upload_ckeditor', event)
        super().__init__(*args, **kwargs)
        if self.event.type_ != EventType.lecture:
            del self.organizer_info
        if self.event.type_ != EventType.conference:
            del self.additional_info

    def validate_contact_emails(self, field):
        for email in field.data:
            if not validate_email(email):
                raise ValidationError(_('Invalid email address: {}').format(escape(email)))


class EventClassificationForm(IndicoForm):
    keywords = IndicoTagListField(_('Keywords'))
    references = ReferencesField(_('External IDs'), reference_class=EventReference)
    label = QuerySelectField(_('Label'), allow_blank=True, get_label='title')
    label_message = TextAreaField(_('Label message'),
                                  description=_('You can optionally provide a message that is shown when hovering '
                                                'the selected label.'))

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super().__init__(*args, **kwargs)
        if event.type_ != EventType.meeting or not ReferenceType.query.has_rows():
            del self.references
        self.label.query = EventLabel.query.order_by(db.func.lower(EventLabel.title))
        if not self.label.query.has_rows():
            del self.label
            del self.label_message


class EventPrivacyForm(IndicoForm):
    _data_controller_fields = ('data_controller_name', 'data_controller_email')
    _privacy_policy_fields = ('privacy_policy_urls', 'privacy_policy')
    data_controller_name = StringField(_('Person/Institution'))
    data_controller_email = EmailField(_('Contact email'), [Optional(), Email()])
    privacy_policy_urls = IndicoLinkListField(_('External page'),
                                              description=_('List of URLs to external pages containing privacy '
                                                            'notices.'))
    privacy_policy = TextAreaField(_('Text'), widget=CKEditorWidget(),
                                   description=_('Only used if no URL is provided'))

    def validate_privacy_policy(self, field):
        if self.privacy_policy_urls.data and self.privacy_policy.data:
            raise ValidationError(_('Define either a privacy notice text or URLs'))


class EventProtectionForm(IndicoForm):
    permissions = PermissionsField(_('Permissions'), object_type='event')
    protection_mode = IndicoProtectionField(_('Protection mode'),
                                            protected_object=lambda form: form.protected_object,
                                            acl_message_url=lambda form: url_for('event_management.acl_message',
                                                                                 form.protected_object))
    access_key = IndicoPasswordField(_('Access key'), toggle=True,
                                     description=_('It is more secure to use only the ACL and not set an access key. '
                                                   '<strong>It will have no effect if the event is not '
                                                   'protected</strong>'))
    own_no_access_contact = StringField(_('No access contact'),
                                        description=_('Contact information shown when someone lacks access to the '
                                                      'event'))
    visibility = SelectField(_('Visibility'), [Optional()], coerce=lambda x: None if x == '' else int(x),
                             description=_('''From which point in the category tree this event will be visible from '''
                                           '''(number of categories upwards). Applies to "Today's events", '''
                                           '''Calendar. If the event is moved, this number will be preserved. '''
                                           '''The "Invisible" option will also hide the event from the category's '''
                                           '''event list except for managers.'''))
    public_regform_access = BooleanField(_('Public registration'), widget=SwitchWidget(),
                                         description=_('Allow users who cannot access the event to register. This will '
                                                       'expose open registration forms to anyone with a link to the '
                                                       'event, so you can let users register without giving access '
                                                       'to anything else in your event.'))
    subcontrib_speakers = BooleanField(_('Speakers can submit'), widget=SwitchWidget(),
                                       description=_('Subcontribution speakers can edit minutes and upload materials.'))
    priv_fields = set()

    def __init__(self, *args, **kwargs):
        self.protected_object = self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)
        if not self.event.category:
            del self.visibility
        else:
            self._init_visibility(self.event)

    def _get_event_own_visibility_horizon(self, event):
        if self.visibility.data is None:  # unlimited
            return Category.get_root()
        elif self.visibility.data == 0:  # invisible
            return None
        else:
            return event.category.nth_parent(self.visibility.data - 1)

    def _init_visibility(self, event):
        assert event.category

        self.visibility.choices = get_visibility_options(event, allow_invisible=True)
        # Check if event visibility would be affected by any of the categories
        real_horizon = event.category.real_visibility_horizon
        own_horizon = self._get_event_own_visibility_horizon(event)
        if own_horizon and real_horizon and real_horizon.is_descendant_of(own_horizon):
            self.visibility.warning = _("This event's visibility is currently limited by that of '{}'.").format(
                real_horizon.title)

    def validate_permissions(self, field):
        except_msg = check_permissions(self.event, field, allow_networks=True)
        if except_msg:
            raise ValidationError(except_msg)

    @classmethod
    def _create_coordinator_priv_fields(cls):
        for name, title in sorted(COORDINATOR_PRIV_TITLES.items(), key=itemgetter(1)):
            setattr(cls, name, BooleanField(title, widget=SwitchWidget(), description=COORDINATOR_PRIV_DESCS[name]))
            cls.priv_fields.add(name)


EventProtectionForm._create_coordinator_priv_fields()


class PosterPrintingForm(IndicoForm):
    template = SelectField(_('Template'))
    margin_horizontal = FloatField(_('Horizontal margins'), [InputRequired()], default=0)
    margin_vertical = FloatField(_('Vertical margins'), [InputRequired()], default=0)
    page_size = IndicoEnumSelectField(_('Page size'), enum=PageSize, default=PageSize.A4, sorted=True)

    def __init__(self, event, **kwargs):
        all_templates = set(event.designer_templates) | get_inherited_templates(event)
        poster_templates = [tpl for tpl in all_templates if tpl.type.name == 'poster']
        super().__init__(**kwargs)
        self.template.choices = sorted(((str(tpl.id), tpl.title) for tpl in poster_templates), key=itemgetter(1))


class CloneRepeatabilityForm(IndicoForm):
    repeatability = IndicoRadioField(_('How to repeat'), choices=CLONE_REPEAT_CHOICES, coerce=lambda x: x or None)


class CloneContentsForm(CloneRepeatabilityForm):
    selected_items = IndicoSelectMultipleCheckboxField(_('What to clone'))
    refresh_users = BooleanField(_('Refresh user information'),
                                 description=_('When checked, names and affiliations of users in the cloned event will '
                                               'be synchronized with their Indico user profiles.'))

    def __init__(self, event, set_defaults=False, **kwargs):
        visible_options = list(filter(attrgetter('is_visible'), EventCloner.get_cloners(event)))
        default_selected_items = kwargs.get('selected_items', [option.name for option in visible_options
                                                               if option.is_default and option.is_available])

        if set_defaults:
            default_category = kwargs['category']['id'] if 'category' in kwargs else None
            form_params = {
                'repeatability': request.form.get('repeatability', kwargs.pop('repeatability', None)),
                'selected_items': (request.form.getlist('selected_items') or default_selected_items),
                'refresh_users': 'refresh_users' in request.form if 'selected_items' in request.form else True,
                'category': request.form.get('category', default_category),
                'csrf_token': request.form.get('csrf_token')
            }
            kwargs['formdata'] = ImmutableMultiDict(form_params)

        super().__init__(**kwargs)
        self.selected_items.choices = [(option.name, option.friendly_name) for option in visible_options]
        self.selected_items.disabled_choices = [option.name for option in visible_options if not option.is_available]


class CloneCategorySelectForm(CloneContentsForm):
    category = CategoryField(_('Category'), require_event_creation_rights=True)

    def validate_category(self, field):
        if not field.data:
            raise ValidationError(_('You have to select a category'))
        elif not field.data.can_create_events(session.user):
            raise ValidationError(_("You can't create events in this category"))


class CloneRepeatFormBase(CloneCategorySelectForm):
    def _calc_start_dt(self, event):
        local_now_date = now_utc().astimezone(event.tzinfo).date()
        local_now_naive = now_utc().astimezone(event.tzinfo).replace(tzinfo=None)
        if event.start_dt_local.date() >= local_now_date:
            # we have to add the timedelta to the naive datetime to avoid
            # dst changes between the old and new dates to change the time
            # of the event
            start_dt = event.start_dt_local.replace(tzinfo=None) + timedelta(days=7)
        else:
            start_dt = datetime.combine(local_now_date, event.start_dt_local.time())
        if start_dt < local_now_naive:
            # if the combination of 'today' with the original start time is
            # still in the past, then let's set it for tomorrow instead
            start_dt += timedelta(days=1)
        return event.tzinfo.localize(start_dt)

    def __init__(self, event, **kwargs):
        kwargs['start_dt'] = self._calc_start_dt(event)
        super().__init__(event, **kwargs)


class CloneRepeatOnceForm(CloneRepeatFormBase):
    start_dt = IndicoDateTimeField(_('Starting'), allow_clear=False)


class CloneRepeatUntilFormBase(CloneRepeatOnceForm):
    stop_criterion = IndicoRadioField(_('Clone'), [DataRequired()], default='num_times',
                                      choices=(('day', _('Until a given day (inclusive)')),
                                               ('num_times', _('A number of times'))))
    until_dt = IndicoDateField(_('Day'), [HiddenUnless('stop_criterion', 'day'), DataRequired()])
    num_times = IntegerField(_('Number of times'),
                             [HiddenUnless('stop_criterion', 'num_times'), DataRequired(),
                              NumberRange(1, 100, message=_('You can clone a maximum of 100 times'))],
                             default=2)

    def __init__(self, event, **kwargs):
        kwargs.setdefault('until_dt', (self._calc_start_dt(event) + timedelta(days=14)).date())
        super().__init__(event, **kwargs)


class CloneRepeatIntervalForm(CloneRepeatUntilFormBase):
    recurrence = RelativeDeltaField(_('Every'), [DataRequired()],
                                    units=('years', 'months', 'weeks', 'days'),
                                    default=relativedelta(weeks=1))

    def validate_recurrence(self, field):
        if field.data != abs(field.data):
            raise ValidationError(_('The time period must be positive'))


class CloneRepeatPatternForm(CloneRepeatUntilFormBase):
    week_day = IndicoWeekDayRepetitionField(_('Every'))
    num_months = IntegerField(_('Months'), [DataRequired(), NumberRange(min=1)], default=1,
                              description=_('Number of months between repetitions'))


class ProgramCodesForm(IndicoForm):
    session_template = StringField(_('Sessions'))
    session_block_template = StringField(_('Session blocks'))
    contribution_template = StringField(_('Contributions'))
    subcontribution_template = StringField(_('Subcontributions'))


class ImportSourceEventForm(IndicoForm):
    source_event_url = URLField(_('Event URL'), [DataRequired(), URL()])


class ImportContentsForm(ImportSourceEventForm):
    selected_items = IndicoSelectMultipleCheckboxField(_('What to clone'))

    def __init__(self, source_event, target_event, set_defaults=False, **kwargs):
        cloners = EventCloner.get_cloners(source_event)
        visible_options = [cloner for cloner in cloners if cloner.is_visible and not cloner.new_event_only]
        conflicts = {cloner.name: cloner.get_conflicts(target_event) for cloner in cloners}
        cloners_with_conflicts = {name for name in conflicts if conflicts[name]}

        if set_defaults:
            form_params = {
                'source_event_url': request.form.get('source_event_url', kwargs.pop('source_event_url', None)),
                'selected_items': request.form.getlist('selected_items'),
                'csrf_token': request.form.get('csrf_token')
            }
            kwargs['formdata'] = ImmutableMultiDict(form_params)

        super().__init__(**kwargs)
        self.selected_items.choices = [(option.name, option.friendly_name) for option in visible_options]
        # We disable all cloners that are not available, handle only cloning to new events,
        # have conflicts with target_event or any of their dependencies have conflicts with target_event
        disabled_choices = []
        reasons = {}
        for option in visible_options:
            if not option.is_available:
                disabled_choices.append(option.name)
                reasons[option.name] = _('There is nothing to import')
            elif conflict := conflicts[option.name]:
                disabled_choices.append(option.name)
                reasons[option.name] = '\n'.join(conflict)
            elif cloners_with_conflicts & option.requires_deep:
                disabled_choices.append(option.name)
                reasons[option.name] = _('This option depends on other options which are unavailable')

        self.selected_items.disabled_choices = disabled_choices
        self.selected_items.disabled_choices_reasons = reasons
