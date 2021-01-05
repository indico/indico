# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.admin.views import WPAdmin
from indico.util.i18n import _
from indico.web.breadcrumbs import render_breadcrumbs
from indico.web.views import WPDecorated, WPJinjaMixin


class WPSettings(WPAdmin):
    template_prefix = 'core/'
    bundles = ('module_cephalopod.js',)


class WPContact(WPJinjaMixin, WPDecorated):
    template_prefix = 'core/'

    def _get_breadcrumbs(self):
        return render_breadcrumbs(_('Contact'))

    def _get_body(self, params):
        return self._get_page_content(params)
