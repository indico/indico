# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.views import WPConferenceDisplayBase


class WPManageSessions(WPEventManagement):
    template_prefix = 'events/sessions/'
    sidemenu_option = 'sessions'
    bundles = ('module_events.sessions.js',)


class WPDisplaySession(WPConferenceDisplayBase):
    template_prefix = 'events/sessions/'
    menu_entry_name = 'timetable'
    bundles = ('module_events.sessions.js',)


class WPDisplayMySessionsConference(WPDisplaySession):
    menu_entry_name = 'my_sessions'
