# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, session
from marshmallow import INCLUDE, fields
from marshmallow_enum import EnumField

from indico.modules.categories.controllers.base import RHDisplayCategoryBase
from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.search.base import SearchOptions, SearchTarget, get_search_provider
from indico.modules.search.internal import InternalSearch
from indico.modules.search.result_schemas import ResultSchema
from indico.modules.search.views import WPCategorySearch, WPEventSearch, WPSearch
from indico.util.marshmallow import validate_with_message
from indico.web.args import use_kwargs
from indico.web.rh import RH


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
        'page': fields.Int(load_default=None),
        'q': fields.String(required=True),
        'type': fields.List(EnumField(SearchTarget), required=True),
        'admin_override_enabled': fields.Bool(
            load_default=False,
            validate=validate_with_message(lambda value: session.user and session.user.is_admin,
                                           'Restricted to admins')
        ),
    }, location='query', unknown=INCLUDE)
    def _process(self, page, q, type, **params):
        search_provider = get_search_provider()
        if type == [SearchTarget.category]:
            search_provider = InternalSearch
        result = search_provider().search(q, session.user, page, type, **params)
        return ResultSchema().dump(result)


class RHAPISearchOptions(RH):
    def _process(self):
        search_provider = get_search_provider()()
        placeholders = search_provider.get_placeholders()
        sort_options = search_provider.get_sort_options()
        return jsonify(SearchOptions(placeholders, sort_options).dump())
