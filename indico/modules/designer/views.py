# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.categories.views import WPCategoryManagement
from indico.modules.events.management.views import WPEventManagement


class WPEventManagementDesigner(WPEventManagement):
    template_prefix = 'designer/'
    bundles = ('module_designer.js',)


class WPCategoryManagementDesigner(WPCategoryManagement):
    template_prefix = 'designer/'
    bundles = ('module_designer.js',)
