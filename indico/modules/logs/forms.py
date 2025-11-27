# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms.fields import StringField, TextAreaField
from wtforms.validators import DataRequired

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import TinyMCEWidget


class ResendEmailPrefaceForm(IndicoForm):
    subject = StringField(_('Subject'), [DataRequired()])
    preface = TextAreaField(_('Preface'),
                            description=_('Explain why you are resending this email. '
                                          'The text will be placed before the original message.'))

    def __init__(self, *args, is_html_email=False, **kwargs):
        super().__init__(*args, **kwargs)
        if is_html_email:
            self.preface.widget = TinyMCEWidget(absolute_urls=True, height=300)
