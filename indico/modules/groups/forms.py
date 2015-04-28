# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from wtforms.fields import StringField, BooleanField, SelectField
from wtforms.validators import DataRequired, ValidationError

from indico.core.db import db
from indico.modules.groups.models.groups import LocalGroup
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import PrincipalField


class SearchForm(IndicoForm):
    provider = SelectField(_('Provider'))
    name = StringField(_('Group name'), [DataRequired()])
    exact = BooleanField(_('Exact match'))


class EditGroupForm(IndicoForm):
    name = StringField(_('Group name'), [DataRequired()])
    members = PrincipalField(_('Group members'), serializable=False)

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group', None)
        super(EditGroupForm, self).__init__(*args, **kwargs)

    def validate_name(self, field):
        query = LocalGroup.find(db.func.lower(LocalGroup.name) == field.data.lower())
        if self.group:
            query = query.filter(LocalGroup.id != self.group.id)
        if query.count():
            raise ValidationError(_('A group with this name already exists.'))
