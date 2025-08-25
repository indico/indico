# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime

from wtforms.fields import BooleanField, TextAreaField
from wtforms.validators import DataRequired, Optional

from indico.util.date_time import server_to_utc
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields.datetime import IndicoDateTimeField
from indico.web.forms.validators import DateTimeRange, LinkedDateTime, UsedIf
from indico.web.forms.widgets import SwitchWidget


class AnnouncementForm(IndicoForm):
    enabled = BooleanField(_('Enabled'), widget=SwitchWidget())
    message = TextAreaField(_('Message'), [UsedIf(lambda form, _: form.enabled.data), DataRequired()],
                            description=_('You may use Markdown and basic HTML elements for formatting.'))

    test_start_dt = IndicoDateTimeField('Start', [DataRequired(),
                                                  DateTimeRange(earliest=server_to_utc(datetime(2025, 8, 20)),
                                                                latest=server_to_utc(datetime(2025, 9, 28)))])
    test_end_dt = IndicoDateTimeField('End', [Optional(), LinkedDateTime('test_start_dt'),
                                              DateTimeRange(earliest=None,
                                                            latest=server_to_utc(datetime(2025, 10, 1, 15)))],
                                       allow_clear=True)
