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

from __future__ import unicode_literals

import operator
from collections import OrderedDict

from flask import request
from MaKaC.accessControl import AccessWrapper

from indico.util.event import truncate_path
from indico.util.redis import write_client as redis_write_client
from indico.util.redis import suggestions
from MaKaC.conference import CategoryManager


def get_related_categories(user):
    """Gets the related categories of a user for the dashboard"""
    favorites = user.favorite_categories
    managed = user.get_linked_objects('category', 'manager')
    res = {}
    for categ in favorites | managed:
        res[(categ.getTitle(), categ.getId())] = {
            'categ': categ,
            'favorite': categ in favorites,
            'managed': categ in managed,
            'path': truncate_path(categ.getCategoryPathTitles(), 30, False)
        }
    return OrderedDict(sorted(res.items(), key=operator.itemgetter(0)))


def get_suggested_categories(user):
    """Gets the suggested categories of a user for the dashboard"""
    if not redis_write_client:
        return []
    related = user.favorite_categories | user.get_linked_objects('category', 'manager')
    res = []
    for id_, score in suggestions.get_suggestions(user, 'category').iteritems():
        try:
            categ = CategoryManager().getById(id_)
        except KeyError:
            suggestions.unsuggest(user, 'category', id_)
            continue
        if not categ or categ.isSuggestionsDisabled() or categ in related:
            continue
        if any(p.isSuggestionsDisabled() for p in categ.iterParents()):
            continue
        # TODO: enable once there's a user.avatar property returning a wrapper with Avatar-style methods
        # if not categ.canAccess(AccessWrapper(user.avatar, request.remote_addr)):
        #     continue
        res.append({
            'score': score,
            'categ': categ,
            'path': truncate_path(categ.getCategoryPathTitles(), 30, False)
        })
    return res
