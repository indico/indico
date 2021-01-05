# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.admin.views import WPAdmin
from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.views import WPConferenceDisplayBase


class WPPaymentAdmin(WPAdmin):
    template_prefix = 'events/payment/'


class WPPaymentEventManagement(WPEventManagement):
    template_prefix = 'events/payment/'
    sidemenu_option = 'payment'


class WPPaymentEvent(WPConferenceDisplayBase):
    template_prefix = 'events/payment/'
    menu_entry_name = 'registration'
