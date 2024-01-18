# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from dataclasses import dataclass

from flask import render_template, session

from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.util import url_for_index


@dataclass(frozen=True)
class Breadcrumb:
    """A breadcrumb to be rendered by the template.

    If `url` is present, the breadcrumb will be a link to it.

    If `icon` is present, the breadcrumb will include the specified icon after the
    title.
    """

    title: str
    url: str = None
    icon: str = None


def render_breadcrumbs(*titles, category=None, event=None, management=False, category_url_factory=None):
    """Render the breadcrumb navigation.

    :param titles: A list of titles, either strings or Breadcrumb objects.
                   If present, these will simply create a trail of breadcrumbs.
                   A 'Home' element is inserted automatically.
    :param event: Generate the event/category breadcrumb trail starting
                  at the specified event.
    :param category: Generate the category breadcrumb trail starting at
                     the specified category.
    :param category_url_factory: Function to get the URL for a category
                                 breadcrumb. If missing, the standard
                                 category url will be used.
    :param management: Whether the event/category breadcrumb trail
                       should link to management pages.
    """
    assert titles or event or category

    if not category and not event:
        items = [Breadcrumb(_('Home'), url_for_index())]
    elif event and event.is_unlisted:
        assert category is None
        items = []
        items.append(Breadcrumb(_('My unlisted events'), url_for('users.user_dashboard')))
        items.append(Breadcrumb(event.title, url_for('event_management.settings', event) if management else event.url,
                                'icon-unlisted-event'))
    else:
        items = []
        if event:
            items.append(Breadcrumb(event.title,
                                    url_for('event_management.settings', event) if management else event.url))
            category = event.category
        if category_url_factory is None:
            category_url_factory = lambda cat, management: (url_for('categories.manage_content', cat)
                                                            if management and cat.can_manage(session.user)
                                                            else cat.url)
        for cat in category.chain_query[::-1]:
            items.append(Breadcrumb(cat.title, category_url_factory(cat, management=management)))
        items.reverse()

    items += [Breadcrumb(title) if isinstance(title, str) else title for title in titles]
    return render_template('breadcrumbs.html', items=items, management=management)
