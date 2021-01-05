# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.models.events import EventType
from indico.modules.events.views import WPConferenceDisplayBase, WPSimpleEventDisplayBase
from indico.web.views import WPJinjaMixin


class WPManageRegistration(WPEventManagement):
    template_prefix = 'events/registration/'
    bundles = ('module_events.registration.js',)

    def __init__(self, rh, event_, active_menu_item=None, **kwargs):
        self.regform = kwargs.get('regform')
        self.registration = kwargs.get('registration')
        WPEventManagement.__init__(self, rh, event_, active_menu_item, **kwargs)

    @property
    def sidemenu_option(self):
        if self.event.type_ != EventType.conference:
            regform = self.regform
            if not regform:
                if self.registration:
                    regform = self.registration.registration_form
            if regform and regform.is_participation:
                return 'participants'
        return 'registration'


class WPManageRegistrationStats(WPManageRegistration):
    bundles = ('statistics.js', 'statistics.css')


class WPManageParticipants(WPManageRegistration):
    sidemenu_option = 'participants'


class DisplayRegistrationFormMixin(WPJinjaMixin):
    template_prefix = 'events/registration/'
    base_class = None

    def _get_body(self, params):
        return WPJinjaMixin._get_page_content(self, params)


class WPDisplayRegistrationFormConference(DisplayRegistrationFormMixin, WPConferenceDisplayBase):
    template_prefix = 'events/registration/'
    base_class = WPConferenceDisplayBase
    menu_entry_name = 'registration'
    bundles = ('module_events.registration.js',)


class WPDisplayRegistrationParticipantList(WPDisplayRegistrationFormConference):
    menu_entry_name = 'participants'


class WPDisplayRegistrationFormSimpleEvent(DisplayRegistrationFormMixin, WPSimpleEventDisplayBase):
    template_prefix = 'events/registration/'
    base_class = WPSimpleEventDisplayBase
    bundles = ('module_events.registration.js',)
