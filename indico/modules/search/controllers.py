# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import math

from flask import session
from marshmallow import INCLUDE, fields
from marshmallow_enum import EnumField
from sqlalchemy.orm import undefer

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.groups import GroupProxy
from indico.modules.search.base import IndicoSearchProvider, SearchTarget, get_search_provider
from indico.modules.search.schemas import DetailedCategorySchema, EventSchema
from indico.modules.search.views import WPSearch
from indico.util.caching import memoize_redis
from indico.web.args import use_kwargs
from indico.web.rh import RH


@memoize_redis(3600)
def get_groups(user):
    access = [user.identifier] + [x.identifier for x in user.local_groups]
    if user.can_get_all_multipass_groups:
        access += [GroupProxy(x.name, x.provider.name, x).identifier
                   for x in user.iter_all_multipass_groups()]
    return access


class RHSearchDisplay(RH):
    def _process(self):
        return WPSearch.render_template('search.html')


class RHAPISearch(RH):
    @use_kwargs({
        'page': fields.Int(missing=1),
        'q': fields.String(required=True),
    }, location='query', unknown=INCLUDE)
    @use_kwargs({'type': EnumField(SearchTarget)}, location='view_args')
    def _process(self, type, page, q, **params):
        search_provider = get_search_provider()
        if not search_provider or type == SearchTarget.category:
            search_provider = InternalSearch
        access = get_groups(session.user) if session.user else []
        total, pages, results, aggs = search_provider().search(q, access, type, page, params)
        return {
            'total': total,
            'pages': pages,
            'results': results,
            'aggregations': aggs
        }


class InternalSearch(IndicoSearchProvider):
    def search(self, query, access, object_type=SearchTarget.event, page=1, params=None):
        # Without any search provider, internally we only support categories and events
        if object_type == SearchTarget.category:
            total, results = InternalSearch.search_categories(page, query)
        elif object_type == SearchTarget.event:
            total, results = InternalSearch.search_events(page, query)
        else:
            total, results = 0, []
        return total, math.ceil(total / self.RESULTS_PER_PAGE), results, {}

    @staticmethod
    def search_categories(page, q):
        results = (Category.query
                   .filter(Category.title_matches(q),
                           ~Category.is_deleted)
                   .options(undefer('chain'))
                   .order_by(db.func.lower(Category.title))
                   .paginate(page, IndicoSearchProvider.RESULTS_PER_PAGE))
        # XXX should we only show categories the user can access?
        # this would be nicer but then we can't easily paginate...
        return results.total, DetailedCategorySchema(many=True).dump(results.items)

    @staticmethod
    def search_events(page, q):
        results = (Event.query
                   .filter(Event.title_matches(q),
                           Event.effective_protection_mode == ProtectionMode.public,
                           ~Event.is_deleted)
                   .order_by(db.func.lower(Event.title))
                   .paginate(page, IndicoSearchProvider.RESULTS_PER_PAGE))
        return results.total, EventSchema(many=True).dump(results.items)
