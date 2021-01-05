# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms import BooleanField, StringField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.validators import UsedIfChecked
from indico.web.forms.widgets import SwitchWidget


class CephalopodForm(IndicoForm):
    joined = BooleanField('Join the community', widget=SwitchWidget())
    contact_name = StringField('Contact Name', [UsedIfChecked('joined'), DataRequired()],
                               description=_('Name of the person responsible for your Indico server.'))
    contact_email = EmailField('Contact Email',
                               [UsedIfChecked('joined'), DataRequired(), Email()],
                               description=_('Email address of the person responsible for your Indico server.'))
