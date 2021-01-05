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

from indico.modules.auth.forms import LocalRegistrationForm
from indico.util.i18n import _
from indico.web.forms.validators import UsedIfChecked
from indico.web.forms.widgets import SwitchWidget


class BootstrapForm(LocalRegistrationForm):
    first_name = StringField('First Name', [DataRequired()])
    last_name = StringField('Last Name', [DataRequired()])
    email = EmailField(_('Email address'), [DataRequired(), Email()])
    affiliation = StringField('Affiliation', [DataRequired()])
    enable_tracking = BooleanField('Join the community', widget=SwitchWidget())
    contact_name = StringField('Contact Name', [UsedIfChecked('enable_tracking'), DataRequired()])
    contact_email = EmailField('Contact Email Address', [UsedIfChecked('enable_tracking'), DataRequired(), Email()])
