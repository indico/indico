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


class WPLegalMixin:
    template_prefix = 'legal/'


class WPManageLegalMessages(WPLegalMixin, WPAdmin):
    pass


class WPDisplayTOS(WPLegalMixin, WPJinjaMixin, WPDecorated):
    def _get_breadcrumbs(self):
        return render_breadcrumbs(_('Terms and Conditions'))

    def _get_body(self, params):
        return self._get_page_content(params)


class WPDisplayPrivacyPolicy(WPLegalMixin, WPJinjaMixin, WPDecorated):
    def _get_breadcrumbs(self):
        return render_breadcrumbs(_('Privacy Policy'))

    def _get_body(self, params):
        return self._get_page_content(params)
