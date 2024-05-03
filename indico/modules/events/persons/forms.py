# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms.fields import BooleanField

from indico.core.auth import multipass
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget


class ManagePersonListsForm(IndicoForm):
    disallow_custom_persons = BooleanField(_('Disallow manually entering persons'), widget=SwitchWidget(),
                                           description=_('Prohibit submitters from adding new speakers/authors '
                                                         'manually and only allow searching for existing users.'))
    default_search_external = BooleanField(_('Include users with no Indico account by default'), widget=SwitchWidget(),
                                           description=_('If enabled, searching people for speakers/authors will '
                                                         'include those with no Indico account by default.'))
    show_titles = BooleanField(_('Show titles'), widget=SwitchWidget(),
                               description=_('When disabled, the titles of persons participating in the event will not '
                                             'be displayed in public areas.'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not any(auth.supports_search for auth in multipass.identity_providers.values()):
            del self.default_search_external
