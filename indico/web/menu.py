# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals, absolute_import

from flask import request
from operator import attrgetter

from indico.util.struct.iterables import group_list
from indico.util.string import return_ascii
from indico.web.flask.util import url_for


class HeaderMenuEntry(object):
    """Defines a header menu entry.

    :param url: the url the menu item points to
    :param caption: the caption of the menu item
    :param parent: when used, all menu entries with the same parent
                   are shown in a dropdown with the parent name as its
                   caption
    """

    def __init__(self, url, caption, parent=None):
        self.url = url
        self.caption = caption
        self.parent = parent

    @return_ascii
    def __repr__(self):
        return '<HeaderMenuEntry({}, {}, {})>'.format(self.caption, self.parent, self.url)

    @classmethod
    def group(cls, entries):
        """Returns the given entries grouped by its parent"""
        return sorted(group_list(entries, key=attrgetter('parent'), sort_by=attrgetter('caption')).items())


class MenuItem(object):
    """Defines a generic menu item

    :param title: the title of the item
    :param endpoint: shortcut to define a menu item that points to the
                     specified endpoint and is considered active only
                     on that endpoints. Cannot be combined with `url` or
                     `endpoints`.
    :param url: url of the menu item
    :param endpoints: set of endpoints on which this menu item is considered
                      active. Can also be a string if only one endpoint is
                      used.
    """

    def __init__(self, title, endpoint=None, url=None, endpoints=None):
        self.title = title
        self.url = url
        if endpoint is not None:
            assert url is None and endpoints is None
            self.url = url_for(endpoint)
            self.endpoints = {endpoint}
        elif endpoints is None:
            self.endpoints = set()
        elif isinstance(endpoints, basestring):
            self.endpoints = {endpoints}
        else:
            self.endpoints = set(endpoints)

    @return_ascii
    def __repr__(self):
        return '<MenuItem({}, {})>'.format(self.title, self.url)

    @property
    def active(self):
        return request.endpoint in self.endpoints
