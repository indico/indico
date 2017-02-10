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
from datetime import timedelta
from operator import itemgetter, attrgetter

from pytz import timezone
from wtforms import BooleanField, StringField, FloatField, SelectField, TextAreaField
from wtforms.validators import InputRequired, DataRequired, ValidationError, Optional

from indico.core.config import Config
from indico.core.db import db
from indico.modules.designer import PageSize
from indico.modules.designer.util import get_inherited_templates
from indico.modules.events import Event, LegacyEventMapping
from indico.modules.events.models.events import EventType
from indico.modules.events.sessions import COORDINATOR_PRIV_TITLES, COORDINATOR_PRIV_DESCS
from indico.modules.events.timetable.util import get_top_level_entries
from indico.util.date_time import format_human_timedelta
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (AccessControlListField, IndicoProtectionField, PrincipalListField,
                                     IndicoEnumSelectField,
                                     IndicoPasswordField, IndicoDateTimeField, IndicoTimezoneSelectField)
from indico.web.forms.validators import LinkedDateTime
from indico.web.forms.widgets import SwitchWidget, CKEditorWidget


class EventDataForm(IndicoForm):
    title = StringField(_('Event title'), [DataRequired()])
    description = TextAreaField(_('Description'), widget=CKEditorWidget())
    url_shortcut = StringField(_('URL shortcut'), filters=[lambda x: (x or None)])

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(EventDataForm, self).__init__(*args, **kwargs)
        # TODO: Add a custom widget showing the prefix right before the field
        prefix = Config.getInstance().getShortEventURL()
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
    _field_order = ('start_dt', 'end_dt', 'timezone', 'update_timetable', 'override_displayed_dates')
    _displayed_date_fields = ('displayed_start_dt', 'displayed_end_dt')

    timezone = IndicoTimezoneSelectField(_('Timezone'), [DataRequired()])
    start_dt = IndicoDateTimeField(_("Start"), [DataRequired()], allow_clear=False)
    end_dt = IndicoDateTimeField(_("End"), [DataRequired(), LinkedDateTime('start_dt', not_equal=True)],
                                 allow_clear=False)
    update_timetable = BooleanField(_('Update timetable'), widget=SwitchWidget(),
                                    description=_("Move sessions/contributions/breaks in the timetable according "
                                                  "to the new event start time."))
    displayed_start_dt = IndicoDateTimeField(_("Start"), [Optional()], allow_clear=True,
                                             description=_("Specifying this date overrides the start date displayed "
                                                           "on the main conference page."))
    displayed_end_dt = IndicoDateTimeField(_("End"), [Optional(), LinkedDateTime('displayed_start_dt', not_equal=True)],
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
            self.displayed_start_dt.default_time = self.start_dt.data.astimezone(timezone(self.timezone.data)).time()
            self.displayed_end_dt.default_time = self.end_dt.data.astimezone(timezone(self.timezone.data)).time()
        else:
            del self.displayed_start_dt
            del self.displayed_end_dt

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
    submitters = PrincipalListField(_('Submitters'), allow_emails=True, allow_external=True,
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


EventProtectionForm._create_coordinator_priv_fields()
