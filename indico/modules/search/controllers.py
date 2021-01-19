# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import division, unicode_literals

from marshmallow import fields
from sqlalchemy.orm import undefer

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.search.base import IndicoSearchProvider, SearchTarget, get_search_provider
from indico.modules.search.schemas import CategoryResultSchema, EventResultSchema
from indico.modules.search.views import WPSearch
from indico.web.args import use_kwargs
from indico.web.rh import RH


class RHSearchDisplay(RH):
    def _process(self):
        return WPSearch.render_template('search.html')


# TODO: plugin disabled
class RHAPISearch(RH):
    TARGET = None
    USE_PROVIDER = True

    def search(self, page, q):
        return {'page': 0, 'pages': 0, 'total': 0, 'results': []}

    @use_kwargs({
        'page': fields.Int(missing=1),
        'q': fields.String(required=True),
    })
    def _process(self, page, q):
        search_provider = get_search_provider()
        if search_provider and self.USE_PROVIDER:
            results = search_provider.search(q, None, self.TARGET)
        else:
            results = self.search(page, q)

        return results


class RHAPISearchCategory(RHAPISearch):
    TARGET = SearchTarget.category
    USE_PROVIDER = False

    def search(self, page, q):
        results = (Category.query
                   .filter(Category.title_matches(q),
                           ~Category.is_deleted)
                   .options(undefer('chain'))
                   .order_by(db.func.lower(Category.title))
                   .paginate(page, IndicoSearchProvider.RESULTS_PER_PAGE))
        # XXX should we only show categories the user can access?
        # this would be nicer but then we can't easily paginate...
        return CategoryResultSchema().dump(results)


class RHAPISearchEvent(RHAPISearch):
    TARGET = SearchTarget.event

    def search(self, page, q):
        results = (Event.query
                   .filter(Event.title_matches(q),
                           Event.effective_protection_mode == ProtectionMode.public,
                           ~Event.is_deleted)
                   .order_by(db.func.lower(Event.title))
                   .paginate(page, IndicoSearchProvider.RESULTS_PER_PAGE))
        # XXX should we only show categories the user can access?
        # this would be nicer but then we can't easily paginate...
        return EventResultSchema().dump(results)


class RHAPISearchContribution(RHAPISearch):
    TARGET = SearchTarget.contribution


class RHAPISearchAttachment(RHAPISearch):
    TARGET = SearchTarget.attachment
