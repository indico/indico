# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.management.views import WPEventManagement


class WPEventRoles(WPEventManagement):
    template_prefix = 'events/roles/'
    sidemenu_option = 'roles'
    bundles = ('module_events.roles.js',)
