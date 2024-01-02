# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms.fields import BooleanField, TextAreaField
from wtforms.validators import DataRequired

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.validators import UsedIf
from indico.web.forms.widgets import SwitchWidget


class AnnouncementForm(IndicoForm):
    enabled = BooleanField(_('Enabled'), widget=SwitchWidget())
    message = TextAreaField(_('Message'), [UsedIf(lambda form, _: form.enabled.data), DataRequired()],
                            description=_('You may use Markdown and basic HTML elements for formatting.'))
