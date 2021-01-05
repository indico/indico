# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.admin.views import WPAdmin
from indico.modules.users.views import WPUser


class WPAPIAdmin(WPAdmin):
    template_prefix = 'api/'
    sidemenu_option = 'api'


class WPAPIUserProfile(WPUser):
    template_prefix = 'api/'
