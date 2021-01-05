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


class WPManagePapers(MathjaxMixin, WPEventManagement):
    template_prefix = 'events/papers/'
    sidemenu_option = 'papers'
    bundles = ('markdown.js', 'module_events.papers.js')

    def _get_head_content(self):
        return WPEventManagement._get_head_content(self) + MathjaxMixin._get_head_content(self)


class WPDisplayPapersBase(WPConferenceDisplayBase):
    template_prefix = 'events/papers/'
    bundles = ('markdown.js', 'module_events.management.js', 'module_events.papers.js')


class WPDisplayJudgingArea(WPDisplayPapersBase):
    menu_entry_name = 'paper_judging_area'


class WPDisplayReviewingArea(WPDisplayPapersBase):
    menu_entry_name = 'paper_reviewing_area'


class WPDisplayCallForPapers(WPDisplayPapersBase):
    menu_entry_name = 'call_for_papers'


class WPDisplayCallForPapersReact(WPDisplayPapersBase):
    menu_entry_name = 'call_for_papers'
    bundles = ('module_events.papers.css',)
