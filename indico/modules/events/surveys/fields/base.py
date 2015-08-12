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

from wtforms.fields import StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Optional

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget


class FieldConfigForm(IndicoForm):
    # data that is stored directly on the question and not in data
    _common_fields = {'title', 'description', 'help', 'is_required'}

    title = StringField(_('Title'), [DataRequired()], description=_("The title of the question"))
    description = TextAreaField(_('Description'), description=_("The description (shown below the question's field.)"))
    help = TextAreaField(_('Help'), description=_("The help tooltip for the question."))
    is_required = BooleanField(_('Required'), widget=SwitchWidget(),
                               description=_("If the user has to answer the question."))


class SurveyField(object):
    """Base class for an survey form field definition.

    To create a new field, subclass this class and register
    it using the `event.get_survey_fields` signal.

    :param question: A `SurveyQuestion` instance
    """

    #: unique name of the field type
    name = None
    #: plugin containing this field type - assigned automatically
    plugin = None
    #: displayed name of the field type
    friendly_name = None
    #: wtform field class for this field
    wtf_field_class = None
    #: the WTForm used to configure the field
    config_form = FieldConfigForm
    #: the validator to use if the field is required
    required_validator = DataRequired
    #: the validator to use if the field is not required
    not_required_validator = Optional

    def __init__(self, question):
        self.question = question

    def save_config(self, form):
        """Populates an object with the field settings

        :param form: A `FieldConfigForm` instance
        """
        form.populate_obj(self.question, fields=form._common_fields)
        self.question.field_type = self.name
        self.question.field_data = {name: field.data
                                    for name, field in form._fields.iteritems()
                                    if name not in form._common_fields and name != 'csrf_token'}

    def create_wtf_field(self):
        """Returns a WTForms field for this field"""
        return self._make_wtforms_field(self.wtf_field_class, self.validators, **self.wtf_field_kwargs)

    @property
    def validators(self):
        """Returns a list of validators for this field"""
        return None

    @property
    def wtf_field_kwargs(self):
        """Returns a dict of kwargs for this field's wtforms field"""
        return {}

    def _make_wtforms_field(self, field_cls, validators=None, **kwargs):
        """Util to instantiate a WTForms field.

        This creates a field with the proper title, description and
        if applicable a DataRequired validator.

        :param field_cls: A WTForms field class
        :param validators: A list of additional validators
        :param kwargs: kwargs passed to the field constructor
        """
        validators = list(validators) if validators is not None else []
        if self.question.is_required:
            validators.append(self.required_validator())
        elif self.not_required_validator:
            validators.append(self.not_required_validator())
        return field_cls(self.question.title, validators, description=self.question.description, **kwargs)
