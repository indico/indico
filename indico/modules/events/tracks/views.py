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


class WPManageTracks(MathjaxMixin, WPEventManagement):
    template_prefix = 'events/tracks/'
    sidemenu_option = 'program'
    bundles = ('markdown.js', 'module_events.tracks.js')

    def _get_head_content(self):
        return WPEventManagement._get_head_content(self) + MathjaxMixin._get_head_content(self)


class WPDisplayTracks(WPConferenceDisplayBase):
    template_prefix = 'events/tracks/'
    menu_entry_name = 'program'
    bundles = ('markdown.js', 'module_events.tracks.js')
