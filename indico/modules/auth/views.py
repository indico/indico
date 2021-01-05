# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.users.views import WPUser
from indico.web.views import WPDecorated, WPJinjaMixin


class WPAuth(WPJinjaMixin, WPDecorated):
    template_prefix = 'auth/'

    def _get_body(self, params):
        return self._get_page_content(params)


class WPAuthUser(WPUser):
    template_prefix = 'auth/'
