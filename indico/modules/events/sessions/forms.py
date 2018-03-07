# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
from wtforms.fields import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired, ValidationError

from indico.core.db import db
from indico.modules.events.sessions.fields import SessionBlockPersonLinkListField
from indico.modules.events.sessions.models.types import SessionType
from indico.modules.events.util import check_permissions
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from indico.web.forms.colors import get_colors
from indico.web.forms.fields import IndicoLocationField, IndicoPalettePickerField, IndicoProtectionField, TimeDeltaField
from indico.web.forms.fields.principals import PermissionsField
from indico.web.forms.widgets import SwitchWidget


class SessionForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()])
    code = StringField(_('Session code'), description=_('The code that will identify the session in the Book of '
                                                        'Abstracts.'))
    description = TextAreaField(_('Description'))
    default_contribution_duration = TimeDeltaField(_('Default contribution duration'), units=('minutes', 'hours'),
                                                   description=_('Duration that a contribution created within this '
                                                                 'session will have by default.'),
                                                   default=timedelta(minutes=20))
    type = QuerySelectField(_("Type"), get_label='name', allow_blank=True, blank_text=_("No type selected"))
    location_data = IndicoLocationField(_("Default location"),
                                        description=_("Default location for blocks inside the session."))
    colors = IndicoPalettePickerField(_('Colours'), color_list=get_colors())

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super(SessionForm, self).__init__(*args, **kwargs)
        if event.type != 'conference':
            del self.code
            del self.type
        else:
            self.type.query = SessionType.query.with_parent(event)
            if not self.type.query.has_rows():
                del self.type


class SessionProtectionForm(IndicoForm):
    permissions = PermissionsField(_("Permissions"), object_type='session')
    protection_mode = IndicoProtectionField(_('Protection mode'), protected_object=lambda form: form.protected_object,
                                            acl_message_url=lambda form: url_for('sessions.acl_message',
                                                                                 form.protected_object))

    def __init__(self, *args, **kwargs):
        self.protected_object = session = kwargs.pop('session')
        self.event = session.event
        super(SessionProtectionForm, self).__init__(*args, **kwargs)

    def validate_permissions(self, field):
        check_permissions(self.event, field)


class SessionBlockForm(IndicoForm):
    title = StringField(_('Title'), description=_('Title of the session block'))
    person_links = SessionBlockPersonLinkListField(_('Conveners'))
    location_data = IndicoLocationField(_('Location'))

    def __init__(self, *args, **kwargs):
        self.session_block = kwargs.pop('session_block', None)
        super(SessionBlockForm, self).__init__(*args, **kwargs)


class MeetingSessionBlockForm(IndicoForm):
    session_title = StringField(_('Title'), [DataRequired()], description=_('Title of the session'))
    block_title = StringField(_('Block title'), description=_('Title of the session block'))
    block_person_links = SessionBlockPersonLinkListField(_('Conveners'))
    block_location_data = IndicoLocationField(_('Location'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.session_block = kwargs.pop('session_block', None)
        super(MeetingSessionBlockForm, self).__init__(*args, **kwargs)

    @property
    def session_fields(self):
        return [field_name for field_name in self._fields if field_name.startswith('session_')]

    @property
    def block_fields(self):
        return [field_name for field_name in self._fields if field_name.startswith('block_')]


class SessionTypeForm(IndicoForm):
    """Form to create or edit a SessionType"""

    name = StringField(_("Name"), [DataRequired()])
    is_poster = BooleanField(_("Poster"), widget=SwitchWidget(),
                             description=_("Whether the session is a poster session or contains normal presentations"))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.session_type = kwargs.get('obj')
        super(SessionTypeForm, self).__init__(*args, **kwargs)

    def validate_name(self, field):
        query = SessionType.query.with_parent(self.event).filter(db.func.lower(SessionType.name) == field.data.lower())
        if self.session_type:
            query = query.filter(SessionType.id != self.session_type.id)
        if query.count():
            raise ValidationError(_("A session type with this name already exists"))
