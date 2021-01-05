# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.views import WPConferenceDisplayBase, WPSimpleEventDisplayBase
from indico.web.views import WPJinjaMixin


class WPManageSurvey(WPEventManagement):
    template_prefix = 'events/surveys/'
    sidemenu_option = 'surveys'
    bundles = ('module_events.surveys.js', 'module_events.surveys.css')


class WPSurveyResults(WPManageSurvey):
    pass


class DisplaySurveyMixin(WPJinjaMixin):
    template_prefix = 'events/surveys/'
    base_class = None

    def _get_body(self, params):
        return WPJinjaMixin._get_page_content(self, params)


class WPDisplaySurveyConference(DisplaySurveyMixin, WPConferenceDisplayBase):
    template_prefix = 'events/surveys/'
    base_class = WPConferenceDisplayBase
    menu_entry_name = 'surveys'
    bundles = ('module_events.surveys.js', 'module_events.surveys.css')


class WPDisplaySurveySimpleEvent(DisplaySurveyMixin, WPSimpleEventDisplayBase):
    template_prefix = 'events/surveys/'
    base_class = WPSimpleEventDisplayBase
    bundles = ('module_events.surveys.js', 'module_events.surveys.css')
