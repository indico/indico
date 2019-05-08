# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import time, timedelta

from flask import session
from wtforms.fields import StringField, TextAreaField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, InputRequired, ValidationError

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.categories.fields import CategoryField
from indico.modules.events.fields import EventPersonLinkListField, IndicoThemeSelectField
from indico.modules.events.models.events import EventType
from indico.modules.events.models.references import ReferenceType
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (IndicoDateTimeField, IndicoEnumRadioField, IndicoLocationField,
                                     IndicoTimezoneSelectField, JSONField, OccurrencesField)
from indico.web.forms.validators import LinkedDateTime
from indico.web.forms.widgets import CKEditorWidget


class ReferenceTypeForm(IndicoForm):
    name = StringField(_("Name"), [DataRequired()], description=_("The name of the external ID type"))
    url_template = URLField(_("URL template"),
                            description=_("The URL template must contain the '{value}' placeholder."))
    scheme = StringField(_("Scheme"), filters=[lambda x: x.rstrip(':') if x else x],
                         description=_("The scheme/protocol of the external ID type"))

    def __init__(self, *args, **kwargs):
        self.reference_type = kwargs.pop('reference_type', None)
        super(ReferenceTypeForm, self).__init__(*args, **kwargs)

    def validate_name(self, field):
        query = ReferenceType.find(db.func.lower(ReferenceType.name) == field.data.lower())
        if self.reference_type:
            query = query.filter(ReferenceType.id != self.reference_type.id)
        if query.count():
            raise ValidationError(_("This name is already in use."))

    def validate_url_template(self, field):
        if field.data and '{value}' not in field.data:
            raise ValidationError(_("The URL template must contain the placeholder '{value}'."))


class EventCreationFormBase(IndicoForm):
    category = CategoryField(_('Category'), [DataRequired()], allow_subcats=False, require_event_creation_rights=True)
    title = StringField(_('Event title'), [DataRequired()])
    timezone = IndicoTimezoneSelectField(_('Timezone'), [DataRequired()])
    location_data = IndicoLocationField(_('Location'), allow_location_inheritance=False, edit_address=False)
    protection_mode = IndicoEnumRadioField(_('Protection mode'), enum=ProtectionMode)
    create_booking = JSONField()

    def validate_category(self, field):
        if not field.data.can_create_events(session.user):
            raise ValidationError(_('You are not allowed to create events in this category.'))


class EventCreationForm(EventCreationFormBase):
    _field_order = ('title', 'start_dt', 'end_dt', 'timezone', 'location_data', 'protection_mode')
    _advanced_field_order = ()
    start_dt = IndicoDateTimeField(_("Start"), [InputRequired()], default_time=time(8), allow_clear=False)
    end_dt = IndicoDateTimeField(_("End"), [InputRequired(), LinkedDateTime('start_dt', not_equal=True)],
                                 default_time=time(18), allow_clear=False)


class LectureCreationForm(EventCreationFormBase):
    _field_order = ('title', 'occurrences', 'timezone', 'location_data', 'person_link_data',
                    'protection_mode')
    _advanced_field_order = ('description', 'theme')
    occurrences = OccurrencesField(_("Dates"), [DataRequired()], default_time=time(8),
                                   default_duration=timedelta(minutes=90))
    person_link_data = EventPersonLinkListField(_('Speakers'))
    description = TextAreaField(_('Description'), widget=CKEditorWidget())
    theme = IndicoThemeSelectField(_('Theme'), event_type=EventType.lecture, allow_default=True)
