# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.fields import StringField
from wtforms.validators import Optional, ValidationError

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoPasswordField
from indico.web.forms.validators import IndicoRegexp


class NotificationSettingsForm(IndicoForm):
    webhook_url = StringField(
        _('Webhook URL'),
        [IndicoRegexp(r'^https://.+'), Optional()],
        description=_("Webhook to contact for notifications.")
    )
    secret_token = IndicoPasswordField(
        _('Secret Token'),
        toggle=True,
        description=_("The bearer token used for authentication with the Webhook.")
    )

    def validate_secret_token(self, field):
        # We shouldn't allow a secret token without a URL
        if field.data and not self.webhook_url.data:
            raise ValidationError(_('You should specify a Webhook URL'))
