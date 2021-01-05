# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.fields import BooleanField, IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, NumberRange

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.validators import HiddenUnless
from indico.web.forms.widgets import CKEditorWidget, SwitchWidget


class NewsSettingsForm(IndicoForm):
    show_recent = BooleanField('Show headlines', widget=SwitchWidget(),
                               description=_('Whether to show the latest news headlines on the Indico home page.'))
    max_entries = IntegerField(_('Max. headlines'), [HiddenUnless('show_recent'), DataRequired(), NumberRange(min=1)],
                               description=_("The maximum number of news headlines to show on the Indico home page."))
    max_age = IntegerField(_('Max. age'), [HiddenUnless('show_recent'), InputRequired(), NumberRange(min=0)],
                           description=_("The maximum age in days for news to show up on the Indico home page. "
                                         "Setting it to 0 will show news no matter how old they are."))
    new_days = IntegerField(_('"New" threshold'), [InputRequired(), NumberRange(min=0)],
                            description=_('The maximum age in days for news to be considered "new". Setting it to 0 '
                                          'will disable the "new" label altogether.'))


class NewsForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()])
    content = TextAreaField(_('Content'), [DataRequired()], widget=CKEditorWidget())
