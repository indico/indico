# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms.fields import TextAreaField, URLField
from wtforms.validators import URL, Optional

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import TinyMCEWidget


class LegalMessagesForm(IndicoForm):
    network_protected_disclaimer = TextAreaField(_('Network-protected information disclaimer'), widget=TinyMCEWidget())
    restricted_disclaimer = TextAreaField(_('Restricted information disclaimer'), widget=TinyMCEWidget())
    tos_url = URLField(_('URL'), [Optional(), URL()],
                       description=_('The URL to an external page with terms and conditions'))
    tos = TextAreaField(_('Text'), widget=TinyMCEWidget(),
                        description=_('Only used if no URL is provided'))
    privacy_policy_url = URLField(_('URL'), [Optional(), URL()],
                                  description=_('The URL to an external page with the privacy policy'))
    privacy_policy = TextAreaField(_('Text'), widget=TinyMCEWidget(),
                                   description=_('Only used if no URL is provided'))
