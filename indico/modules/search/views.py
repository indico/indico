# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.views import WPCategory
from indico.modules.events.views import WPConferenceDisplayBase
from indico.util.i18n import _
from indico.web.breadcrumbs import render_breadcrumbs
from indico.web.views import WPDecorated, WPJinjaMixin


class WPSearchMixin:
    template_prefix = 'search/'
    bundles = ('module_search.js', 'module_search.css')


class WPSearch(WPSearchMixin, WPJinjaMixin, WPDecorated):
    title = _('Search')

    def _get_breadcrumbs(self):
        return render_breadcrumbs(_('Search'))

    def _get_body(self, params):
        return self._get_page_content(params)


class WPCategorySearch(WPSearchMixin, WPCategory):
    """WP for category-scoped search."""

    @property
    def _extra_title_parts(self):
        return [_('Search')]

    def _get_breadcrumbs(self):
        if not self.category or self.category.is_root:
            return ''
        return render_breadcrumbs(_('Search'), category=self.category)


class WPEventSearch(WPSearchMixin, WPConferenceDisplayBase):
    @property
    def _extra_title_parts(self):
        return [_('Search')]
