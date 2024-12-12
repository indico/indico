# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import date

from wtforms.fields import BooleanField, TextAreaField
from wtforms.validators import DataRequired, Optional

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields.datetime import IndicoDateField
from indico.web.forms.validators import DateRange, LinkedDate, UsedIf
from indico.web.forms.widgets import SwitchWidget


class AnnouncementForm(IndicoForm):
    enabled = BooleanField(_('Enabled'), widget=SwitchWidget())
    message = TextAreaField(_('Message'), [UsedIf(lambda form, _: form.enabled.data), DataRequired()],
                            description=_('You may use Markdown and basic HTML elements for formatting.'))

    test_start_date = IndicoDateField('Start', [DataRequired(), DateRange(earliest=date(2025, 4, 5),
                                                                          latest=date(2025, 5, 20))])
    test_end_date = IndicoDateField('End', [Optional(), LinkedDate('test_start_date'),
                                            DateRange(earliest=None, latest=date(2025, 6, 20))],
                                    allow_clear=True)
