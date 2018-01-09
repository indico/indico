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

from wtforms.fields import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired

from indico.util.i18n import _
from indico.web.fields import BaseField
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget


class SurveyFieldConfigForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()], description=_("The title of the question"))
    description = TextAreaField(_('Description'), description=_("The description (shown below the question's field.)"))
    is_required = BooleanField(_('Required'), widget=SwitchWidget(),
                               description=_("If the user has to answer the question."))


class SurveyField(BaseField):
    config_form_base = SurveyFieldConfigForm

    def get_summary(self):
        """Return the summary of answers submitted for this field."""
        raise NotImplementedError

    @staticmethod
    def process_imported_data(data):
        """Process the form's data imported from a dict."""
        return data
