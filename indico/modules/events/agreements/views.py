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


class WPAgreementFormSimpleEvent(WPJinjaMixin, WPSimpleEventDisplayBase):
    template_prefix = 'events/agreements/'

    def _get_body(self, params):
        return self._get_page_content(params)


class WPAgreementFormConference(WPConferenceDisplayBase):
    template_prefix = 'events/agreements/'


class WPAgreementManager(WPEventManagement):
    template_prefix = 'events/agreements/'
    sidemenu_option = 'agreements'
