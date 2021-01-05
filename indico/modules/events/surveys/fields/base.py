# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
