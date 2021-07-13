# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import g, render_template, request

from indico.core import signals
from indico.web.flask.templating import template_hook


@signals.core.app_created.connect
def _check_search_provider(app, **kwargs):
    from .base import get_search_provider
    get_search_provider(only_active=False)


@template_hook('conference-header-right-column')
def _add_conference_search_box(event, **kwargs):
    from indico.modules.events.layout import layout_settings
    if (
        layout_settings.get(event, 'is_searchable') and
        not g.get('static_site') and
        request.endpoint != 'search.event_search'
    ):
        return render_template('search/event_search_bar.html', event=event)
