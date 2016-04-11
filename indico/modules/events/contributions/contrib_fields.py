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

from wtforms.validators import DataRequired

from indico.web.forms.widgets import SwitchWidget
from wtforms.fields import BooleanField, StringField, TextAreaField

from indico.modules.events.contributions.models.fields import ContributionField
from indico.util.i18n import _
from indico.web.fields import BaseField, get_field_definitions
from indico.web.fields.simple import TextField
from indico.web.fields.choices import SingleChoiceField
from indico.web.forms.base import IndicoForm


def get_contrib_field_types():
    """Get a dict containing all contribution field types"""
    return get_field_definitions(ContributionField)


class ContribFieldConfigForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()], description=_("The title of the field"))
    description = TextAreaField(_('Description'), description=_("The description of the field"))
    is_required = BooleanField(_('Required'), widget=SwitchWidget(),
                               description=_("Whether the user has to fill out the field"))
    is_active = BooleanField(_('Active'), widget=SwitchWidget(),
                             description=_("Whether the field is available."),
                             default=True)


class ContribField(BaseField):
    config_form_base = ContribFieldConfigForm
    common_settings = ('title', 'description', 'is_required', 'is_active')


class ContribTextField(TextField, ContribField):
    pass


class ContribSingleChoiceField(SingleChoiceField, ContribField):
    pass
