# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.views import WPCategoryManagement
from indico.modules.events.management.views import WPEventManagement


class WPEventLogs(WPEventManagement):
    bundles = ('module_logs.js', 'module_logs.css')
    template_prefix = 'logs/'
    sidemenu_option = 'logs'


class WPCategoryLogs(WPCategoryManagement):
    bundles = ('module_logs.js', 'module_logs.css')
    template_prefix = 'logs/'
