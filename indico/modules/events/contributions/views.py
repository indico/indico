# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.views import WPConferenceDisplayBase
from indico.util.mathjax import MathjaxMixin


class WPManageContributions(MathjaxMixin, WPEventManagement):
    template_prefix = 'events/contributions/'
    sidemenu_option = 'contributions'
    bundles = ('markdown.js', 'module_events.contributions.js')

    def _get_head_content(self):
        return WPEventManagement._get_head_content(self) + MathjaxMixin._get_head_content(self)


class WPContributionsDisplayBase(WPConferenceDisplayBase):
    template_prefix = 'events/contributions/'
    # 'module_events.contributions.js' is already included via WPEventBase
    bundles = ('markdown.js', 'module_events.contributions.css')


class WPMyContributions(WPContributionsDisplayBase):
    menu_entry_name = 'my_contributions'


class WPContributions(WPContributionsDisplayBase):
    menu_entry_name = 'contributions'


class WPAuthorList(WPContributionsDisplayBase):
    menu_entry_name = 'author_index'


class WPSpeakerList(WPContributionsDisplayBase):
    menu_entry_name = 'speaker_index'
