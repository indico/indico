# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.views import WPConferenceDisplayBase


class WPLayoutEdit(WPEventManagement):
    template_prefix = 'events/layout/'
    sidemenu_option = 'layout'


class WPMenuEdit(WPEventManagement):
    template_prefix = 'events/layout/'
    sidemenu_option = 'menu'
    bundles = ('module_events.layout.js',)


class WPImages(WPEventManagement):
    template_prefix = 'events/layout/'
    sidemenu_option = 'images'


class WPPage(WPConferenceDisplayBase):
    template_prefix = 'events/layout/'

    def __init__(self, rh, conference, **kwargs):
        self.page = kwargs['page']
        WPConferenceDisplayBase.__init__(self, rh, conference, **kwargs)

    @property
    def sidemenu_entry(self):
        return self.page.menu_entry
