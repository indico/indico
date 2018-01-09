# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals

from flask import render_template

from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.util import url_for_index


def render_breadcrumbs(*titles, **kwargs):
    """Render the breadcrumb navigation

    :param titles: A list of plain text titles.  If present, these will
                   simply create a unlinked trail of breadcrumbs.
                   A 'Home' element is inserted automatically.
    :param event: Generate the event/category breadcrumb trail starting
                  at the specified event.
    :param category: Generate the category breadcrumb trail starting at
                     the specified category.
    :param management: Whether the event/category breadcrumb trail
                       should link to management pages.
    """
    category = kwargs.get('category', None)
    event = kwargs.get('event', None)
    management = kwargs.get('management', False)
    assert bool(titles) + bool(event) + bool(category) == 1
    if not category and not event:
        items = [(_('Home'), url_for_index())] + [(x, None) for x in titles]
    else:
        items = []
        if event:
            items.append((event.title, url_for('event_management.settings', event) if management else event.url))
            category = event.category
        for cat in category.chain_query[::-1]:
            items.append((cat.title, url_for('categories.manage_content', cat) if management else cat.url))
        items.reverse()
    return render_template('breadcrumbs.html', items=items, management=management)
