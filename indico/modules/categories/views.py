# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request
from markupsafe import escape

from indico.modules.admin.views import WPAdmin
from indico.util.i18n import _
from indico.util.mathjax import MathjaxMixin
from indico.web.breadcrumbs import render_breadcrumbs
from indico.web.flask.util import url_for
from indico.web.menu import get_menu_item
from indico.web.views import WPDecorated, WPJinjaMixin, render_header


class WPManageUpcomingEvents(WPAdmin):
    template_prefix = 'categories/'


class WPCategory(MathjaxMixin, WPJinjaMixin, WPDecorated):
    """WP for category display pages."""

    template_prefix = 'categories/'
    ALLOW_JSON = False
    bundles = ('module_categories.js', 'module_categories.css')

    def __init__(self, rh, category, **kwargs):
        kwargs['category'] = category
        self.category = category
        self.atom_feed_url = kwargs.get('atom_feed_url')
        self.atom_feed_title = kwargs.get('atom_feed_title')
        if category:
            self.title = category.title
        WPDecorated.__init__(self, rh, **kwargs)
        self._mathjax = kwargs.pop('mathjax', False)

    def _get_header(self):
        return render_header(category=self.category, protected_object=self.category,
                             local_tz=self.category.display_tzinfo.zone)

    def _get_body(self, params):
        return self._get_page_content(params)

    def _get_head_content(self):
        head_content = WPDecorated._get_head_content(self)
        if self.atom_feed_url:
            title = self.atom_feed_title or _('Indico Atom feed')
            head_content += (f'<link rel="alternate" type="application/atom+xml" title="{escape(title)}" '
                             f'href="{self.atom_feed_url}">')
        if self._mathjax:
            head_content += MathjaxMixin._get_head_content(self)
        return head_content

    def _get_breadcrumbs(self):
        if not self.category or self.category.is_root:
            return ''
        return render_breadcrumbs(category=self.category)


class WPCategoryCalendar(WPCategory):
    """WP for category calendar page."""

    bundles = ('module_categories.calendar.js', 'module_categories.calendar.css')

    def _get_breadcrumbs(self):
        return render_breadcrumbs(
            _('Calendar'),
            category=self.category,
            category_url_factory=lambda cat, management: url_for('categories.calendar', cat)
        )


class WPCategoryManagement(WPCategory):
    """WP for category management pages."""

    MANAGEMENT = True
    bundles = ('module_categories.management.js',)

    def __init__(self, rh, category, active_menu_item, **kwargs):
        kwargs['active_menu_item'] = self.active_menu_item = active_menu_item
        WPCategory.__init__(self, rh, category, **kwargs)

    def _get_header(self):
        return render_header(category=self.category, protected_object=self.category,
                             local_tz=self.category.timezone, force_local_tz=True)

    def _get_parent_category_breadcrumb_url(self, category, management=False):
        if not management:
            return category.url
        params = request.view_args | request.args.to_dict(False)
        del params['category_id']
        return url_for(request.endpoint, category, **params)

    def _get_breadcrumbs(self):
        if self.category.is_root:
            return ''
        return render_breadcrumbs(category=self.category, management=True,
                                  category_url_factory=self._get_parent_category_breadcrumb_url)

    @property
    def _extra_title_parts(self):
        title_parts = super()._extra_title_parts
        if menu_item := get_menu_item('category-management-sidemenu', self.active_menu_item, category=self.category):
            return (*title_parts, menu_item.title)
        return title_parts
