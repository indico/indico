# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.management.views import WPEventManagement


class WPEventLogs(WPEventManagement):
    bundles = ('module_events.logs.js', 'module_events.logs.css')
    template_prefix = 'events/logs/'
    sidemenu_option = 'logs'
