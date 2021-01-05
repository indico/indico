# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.fields import BooleanField, StringField
from wtforms.validators import DataRequired

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.validators import IndicoRegexp
from indico.web.forms.widgets import SwitchWidget


class SettingsForm(IndicoForm):
    # Core settings
    core_site_title = StringField(_('Title'), [DataRequired()], description=_("The global title of this Indico site."))
    core_site_organization = StringField(_('Organization'),
                                         description=_("The organization that runs this Indico site."))

    # Social settings
    social_enabled = BooleanField(_('Enabled'), widget=SwitchWidget())
    social_facebook_app_id = StringField('Facebook App ID', [IndicoRegexp(r'^\d*$')])

    @property
    def _fieldsets(self):
        return [
            (_('Site'), [x for x in self._fields if x.startswith('core_')]),
            (_('Social'), [x for x in self._fields if x.startswith('social_')]),
        ]
