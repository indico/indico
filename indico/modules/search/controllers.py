# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import math

from flask import jsonify, session
from marshmallow import INCLUDE, fields
from marshmallow_enum import EnumField
from sqlalchemy.orm import undefer

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.categories import Category
from indico.modules.categories.controllers.base import RHDisplayCategoryBase
from indico.modules.events import Event
from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.groups import GroupProxy
from indico.modules.search.base import IndicoSearchProvider, SearchOptions, SearchTarget, get_search_provider
from indico.modules.search.result_schemas import CategoryResultSchema, EventResultSchema, ResultSchema
from indico.modules.search.schemas import DetailedCategorySchema, EventSchema
from indico.modules.search.views import WPCategorySearch, WPEventSearch, WPSearch
from indico.util.caching import memoize_redis
from indico.web.args import use_kwargs
from indico.web.rh import RH


@memoize_redis(3600)
def get_user_access(user):
    access = [user.identifier] + [u.identifier for u in user.get_merged_from_users_recursive()]
    access += [GroupProxy(x.id, _group=x).identifier for x in user.local_groups]
    if user.can_get_all_multipass_groups:
        access += [GroupProxy(x.name, x.provider.name, x).identifier
                   for x in user.iter_all_multipass_groups()]
    return access


class RHSearchDisplay(RH):
    def _process(self):
        return WPSearch.render_template('search.html')


class RHCategorySearchDisplay(RHDisplayCategoryBase):
    def _process(self):
        return WPCategorySearch.render_template('category_search.html', self.category)


class RHEventSearchDisplay(RHDisplayEventBase):
    def _process(self):
        return WPEventSearch.render_template('event_search.html', self.event)


class RHAPISearch(RH):
    """API for searching across all records with the current search provider.

    Besides pagination, filters or placeholders may be passed as query parameters.
    Since `type` may be a list, the results from the search provider are not mixed with
    the InternalSearch.
    """

    @use_kwargs({
        'page': fields.Int(missing=None),
        'q': fields.String(required=True),
        'type': fields.List(EnumField(SearchTarget), missing=None)
    }, location='query', unknown=INCLUDE)
    def _process(self, page, q, type, **params):
        search_provider = get_search_provider()
        if type == [SearchTarget.category]:
            search_provider = InternalSearch
        access = get_user_access(session.user) if session.user else []
        result = search_provider().search(q, access, page, type, **params)
        return ResultSchema().dump(result)


class RHAPISearchOptions(RH):
    def _process(self):
        search_provider = get_search_provider()()
        placeholders = search_provider.get_placeholders()
        sort_options = search_provider.get_sort_options()
        return jsonify(SearchOptions(placeholders, sort_options).dump())


class InternalSearch(IndicoSearchProvider):
    def search(self, query, access, page=None, object_types=(), **params):
        if object_types == [SearchTarget.category]:
            total, results = InternalSearch.search_categories(page, query, params.get('category_id'))
        elif object_types == [SearchTarget.event]:
            total, results = InternalSearch.search_events(page, query, params.get('category_id'))
        else:
            total, results = 0, []
        return {
            'total': total,
            'pages': math.ceil(total / self.RESULTS_PER_PAGE),
            'results': results,
        }

    @staticmethod
    def search_categories(page, q, category_id):
        query = Category.query if not category_id else Category.get(category_id).deep_children_query

        results = (query
                   .filter(Category.title_matches(q),
                           ~Category.is_deleted)
                   .options(undefer('chain'))
                   .order_by(db.func.lower(Category.title))
                   .paginate(page, IndicoSearchProvider.RESULTS_PER_PAGE))

        # XXX should we only show categories the user can access?
        # this would be nicer but then we can't easily paginate...
        res = DetailedCategorySchema(many=True).dump(results.items)
        return results.total, CategoryResultSchema(many=True).load(res)

    @staticmethod
    def search_events(page, q, category_id):
        filters = [
            Event.title_matches(q),
            Event.effective_protection_mode == ProtectionMode.public,
            ~Event.is_deleted
        ]

        if category_id is not None:
            filters.append(Event.category_chain_overlaps(category_id))

        results = (Event.query
                   .filter(*filters)
                   .order_by(db.func.lower(Event.title))
                   .paginate(page, IndicoSearchProvider.RESULTS_PER_PAGE))

        res = EventSchema(many=True).dump(results.items)
        return results.total, EventResultSchema(many=True).load(res)
