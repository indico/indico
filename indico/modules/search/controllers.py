# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, session
from marshmallow import INCLUDE, fields
from marshmallow_enum import EnumField
from sqlalchemy.orm import subqueryload, undefer

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.core.db.sqlalchemy.util.queries import get_n_matching
from indico.modules.categories import Category
from indico.modules.categories.controllers.base import RHDisplayCategoryBase
from indico.modules.events import Event
from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.groups import GroupProxy
from indico.modules.search.base import IndicoSearchProvider, SearchOptions, SearchTarget, get_search_provider
from indico.modules.search.result_schemas import CategoryResultSchema, EventResultSchema, ResultSchema
from indico.modules.search.schemas import DetailedCategorySchema, HTMLStrippingEventSchema
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
            pagenav, results = self.search_categories(query, page, params.get('category_id'))
        elif object_types == [SearchTarget.event]:
            pagenav, results = self.search_events(query, page, params.get('category_id'))
        else:
            pagenav, results = {}, []
        return {
            'total': -1 if results else 0,
            'pagenav': pagenav,
            'results': results,
        }

    def _paginate(self, query, page, column, user):
        reverse = False
        pagenav = {'prev': None, 'next': None}
        if not page:
            query = query.order_by(column.desc())
        elif page > 0:  # next page
            query = query.filter(column < page).order_by(column.desc())
            # since we asked for a next page we know that a previous page exists
            pagenav['prev'] = -(page - 1)
        elif page < 0:  # prev page
            query = query.filter(column > -page).order_by(column)
            # since we asked for a previous page we know that a next page exists
            pagenav['next'] = -(page - 1)
            reverse = True

        def _can_access(obj):
            return obj.effective_protection_mode == ProtectionMode.public or obj.can_access(user, allow_admin=False)

        res = get_n_matching(query, self.RESULTS_PER_PAGE + 1, _can_access, prefetch_factor=20)

        if len(res) > self.RESULTS_PER_PAGE:
            # we queried 1 more so we can see if there are more results available
            del res[self.RESULTS_PER_PAGE:]
            if reverse:
                pagenav['prev'] = -res[-1].id
            else:
                pagenav['next'] = res[-1].id

        if reverse:
            res.reverse()

        return res, pagenav

    def search_categories(self, q, page, category_id):
        query = Category.query if not category_id else Category.get(category_id).deep_children_query

        query = (query
                 .filter(Category.title_matches(q),
                         ~Category.is_deleted)
                 .options(undefer('chain'),
                          undefer(Category.effective_protection_mode),
                          subqueryload(Category.acl_entries)))

        objs, pagenav = self._paginate(query, page, Category.id, session.user)
        res = DetailedCategorySchema(many=True).dump(objs)
        return pagenav, CategoryResultSchema(many=True).load(res)

    def search_events(self, q, page, category_id):
        filters = [
            Event.title_matches(q),
            ~Event.is_deleted
        ]

        if category_id is not None:
            filters.append(Event.category_chain_overlaps(category_id))

        query = (Event.query
                 .filter(*filters)
                 .options(subqueryload(Event.acl_entries), undefer(Event.effective_protection_mode)))
        objs, pagenav = self._paginate(query, page, Event.id, session.user)
        res = HTMLStrippingEventSchema(many=True).dump(objs)
        return pagenav, EventResultSchema(many=True).load(res)
