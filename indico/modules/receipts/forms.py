# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms import BooleanField

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields.principals import PrincipalListField
from indico.web.forms.widgets import SwitchWidget


class ReceiptsSettingsForm(IndicoForm):
    allow_external_urls = BooleanField(_('External URLs'), widget=SwitchWidget(),
                                       description=_('Allow embedding images from external URLs'))
    authorized_users = PrincipalListField(_('Authorized users'), allow_groups=True,
                                          description=_('These users may create/manage document templates without '
                                                        'being Indico admins'))
