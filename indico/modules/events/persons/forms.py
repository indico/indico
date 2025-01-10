# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms.fields import BooleanField

from indico.core.auth import multipass
from indico.modules.events.persons import CustomPersonsMode
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoEnumSelectField
from indico.web.forms.widgets import SwitchWidget


class ManagePersonListsForm(IndicoForm):
    custom_persons_mode = IndicoEnumSelectField(_('Allow manually adding people'), enum=CustomPersonsMode,
                                                description=_('Controls when users can manually add people to person '
                                                              'lists, such as speakers/authors of contributions.'))
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
