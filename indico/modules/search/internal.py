# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.orm import subqueryload, undefer

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.core.db.sqlalchemy.util.queries import get_n_matching
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.search.base import IndicoSearchProvider, SearchTarget
from indico.modules.search.result_schemas import CategoryResultSchema, EventResultSchema
from indico.modules.search.schemas import DetailedCategorySchema, HTMLStrippingEventSchema


class InternalSearch(IndicoSearchProvider):
    def search(self, query, user=None, page=None, object_types=(), *, admin_override_enabled=False,
               **params):
        category_id = params.get('category_id')
        if object_types == [SearchTarget.category]:
            pagenav, results = self.search_categories(query, user, page, category_id,
                                                      admin_override_enabled)
        elif object_types == [SearchTarget.event]:
            pagenav, results = self.search_events(query, user, page, category_id,
                                                  admin_override_enabled)
        else:
            pagenav, results = {}, []
        return {
            'total': -1 if results else 0,
            'pagenav': pagenav,
            'results': results,
        }

    def _paginate(self, query, page, column, user, admin_override_enabled):
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
            return (obj.effective_protection_mode == ProtectionMode.public or
                    obj.can_access(user, allow_admin=admin_override_enabled))

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

    def search_categories(self, q, user, page, category_id, admin_override_enabled):
        query = Category.query if not category_id else Category.get(category_id).deep_children_query

        query = (query
                 .filter(Category.title_matches(q),
                         ~Category.is_deleted)
                 .options(undefer('chain'),
                          undefer(Category.effective_protection_mode),
                          subqueryload(Category.acl_entries)))

        objs, pagenav = self._paginate(query, page, Category.id, user, admin_override_enabled)
        res = DetailedCategorySchema(many=True).dump(objs)
        return pagenav, CategoryResultSchema(many=True).load(res)

    def search_events(self, q, user, page, category_id, admin_override_enabled):
        filters = [
            Event.title_matches(q),
            ~Event.is_deleted
        ]

        if category_id is not None:
            filters.append(Event.category_chain_overlaps(category_id))

        query = (Event.query
                 .filter(*filters)
                 .options(subqueryload(Event.acl_entries), undefer(Event.effective_protection_mode)))
        objs, pagenav = self._paginate(query, page, Event.id, user, admin_override_enabled)
        res = HTMLStrippingEventSchema(many=True).dump(objs)
        return pagenav, EventResultSchema(many=True).load(res)
