# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms import ValidationError

from indico.util.i18n import _
from indico.web.forms.fields.simple import JSONField
from indico.web.forms.widgets import JinjaWidget


class IndicoPrivacyPolicyURLsField(JSONField):
    widget = JinjaWidget('forms/privacy_policy_urls_widget.html', single_kwargs=True, single_line=True)

    def pre_validate(self, form):
        for item in self.data:
            if len(self.data) > 1 and not item.get('title'):
                raise ValidationError(_('Titles are required when more than one privacy notice is specified'))
            if not item.get('url'):
                raise ValidationError(_('URL is required'))
