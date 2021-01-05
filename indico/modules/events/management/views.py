# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.models.events import EventType
from indico.util.string import strip_tags
from indico.web.breadcrumbs import render_breadcrumbs
from indico.web.flask.templating import get_template_module
from indico.web.views import WPDecorated, WPJinjaMixin, render_header


class WPEventManagement(WPJinjaMixin, WPDecorated):
    """Base class for event management pages.

    When using this class the template will always have `event`
    available; it is not necessary to pass it as a kwarg when calling
    the `render_template` classmethod.

    When using the class directly, pass the menu item as a posarg::

        return WPEventManagement.render_template('foobar.html', self.event, 'foobar',
                                                 foo='bar')

    When subclassing you can set `sidemenu_option` on the class,
    allowing you to omit it.  This is recommended if you have many
    pages using the same menu item or if you already need to subclass
    for some other reason (e.g. to set a `template_prefix` or include
    additional JS/CSS bundles)::

        return WPSomething.render_template('foobar.html', self.event,
                                           foo='bar')
    """

    MANAGEMENT = True
    ALLOW_JSON = False

    bundles = ('module_events.cloning.js', 'module_events.importing.js', 'module_events.management.js')

    def __init__(self, rh, event_, active_menu_item=None, **kwargs):
        assert event_ == kwargs.setdefault('event', event_)
        self.event = event_
        self.title = strip_tags(self.event.title)
        kwargs['base_layout_params'] = {
            'active_menu_item': active_menu_item or self.sidemenu_option,
            'event_types': [(et.name, et.title) for et in EventType]
        }
        WPDecorated.__init__(self, rh, **kwargs)

    def _get_header(self):
        return render_header(category=self.event.category, local_tz=self.event.timezone, force_local_tz=True)

    def _get_body(self, params):
        return self._get_page_content(params)

    def _get_breadcrumbs(self):
        return render_breadcrumbs(event=self.event, management=True)


class WPEventSettings(WPEventManagement):
    template_prefix = 'events/management/'


class WPEventProtection(WPEventManagement):
    template_prefix = 'events/management/'


class WPEventProgramCodes(WPEventManagement):
    template_prefix = 'events/management/'


def render_event_management_header_right(event):
    tpl = get_template_module('events/management/_management_frame.html')
    return tpl.render_event_management_header_right(event=event, event_types=[(et.name, et.title) for et in EventType])
