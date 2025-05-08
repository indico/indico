# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.admin.views import WPAdmin
from indico.modules.categories.views import WPCategoryManagement
from indico.modules.events.management.views import WPEventManagement
from indico.modules.users.views import WPUser


class WPAppLogs(WPAdmin):
    bundles = ('module_logs.js', 'module_logs.css')
    template_prefix = 'logs/'


class WPCategoryLogs(WPCategoryManagement):
    bundles = ('module_logs.js', 'module_logs.css')
    template_prefix = 'logs/'


class WPEventLogs(WPEventManagement):
    bundles = ('module_logs.js', 'module_logs.css')
    template_prefix = 'logs/'
    sidemenu_option = 'logs'


class WPUserLogs(WPUser):
    bundles = ('module_logs.js', 'module_logs.css')
    template_prefix = 'logs/'
