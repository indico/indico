# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.fields import BooleanField, SelectField, StringField
from wtforms.validators import DataRequired, ValidationError

from indico.core.db import db
from indico.modules.groups.models.groups import LocalGroup
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields.principals import PrincipalListField


class SearchForm(IndicoForm):
    provider = SelectField(_('Provider'))
    name = StringField(_('Group name'), [DataRequired()])
    exact = BooleanField(_('Exact match'))


class EditGroupForm(IndicoForm):
    name = StringField(_('Group name'), [DataRequired()])
    members = PrincipalListField(_('Group members'))

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group', None)
        super(EditGroupForm, self).__init__(*args, **kwargs)

    def validate_name(self, field):
        query = LocalGroup.find(db.func.lower(LocalGroup.name) == field.data.lower())
        if self.group:
            query = query.filter(LocalGroup.id != self.group.id)
        if query.count():
            raise ValidationError(_('A group with this name already exists.'))
