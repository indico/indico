# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.fields.core import BooleanField, StringField
from wtforms.validators import DataRequired, InputRequired, Length

from indico.modules.events.models.roles import EventRole
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.colors import get_role_colors
from indico.web.forms.fields import FileField, IndicoSinglePalettePickerField
from indico.web.forms.widgets import SwitchWidget


class EventRoleForm(IndicoForm):
    name = StringField(_('Name'), [DataRequired()],
                       description=_('The full name of the role'))
    code = StringField(_('Code'), [DataRequired(), Length(max=3)], filters=[lambda x: x.upper() if x else ''],
                       render_kw={'style': 'width:60px; text-align:center; text-transform:uppercase;'},
                       description=_('A shortcut (max. 3 characters) for the role'))
    color = IndicoSinglePalettePickerField(_('Colour'), color_list=get_role_colors(), text_color='ffffff',
                                           description=_('The colour used when displaying the role'))

    def __init__(self, *args, **kwargs):
        self.role = kwargs.get('obj')
        self.event = kwargs.pop('event')
        super(EventRoleForm, self).__init__(*args, **kwargs)

    def validate_code(self, field):
        query = EventRole.query.with_parent(self.event).filter_by(code=field.data)
        if self.role is not None:
            query = query.filter(EventRole.id != self.role.id)
        if query.has_rows():
            raise ValueError(_('A role with this code already exists.'))


class ImportMembersCSVForm(IndicoForm):
    source_file = FileField(_('Source File'), [InputRequired(), DataRequired()], accepted_file_types='.csv,.txt')
    remove_existing = BooleanField(_('Remove existing members'), widget=SwitchWidget())
