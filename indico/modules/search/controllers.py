# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from marshmallow import fields
from sqlalchemy.orm import undefer

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.search.schemas import CategoryResultSchema, EventResultSchema
from indico.modules.search.views import WPSearch
from indico.web.args import use_kwargs
from indico.web.rh import RH


RESULTS_PER_PAGE = 10


class RHSearch(RH):
    def _process(self):
        return WPSearch.render_template('search.html')


class RHSearchCategories(RH):
    @use_kwargs({
        'page': fields.Int(missing=1),
        'q': fields.String(required=True),
    })
    def _process(self, page, q):
        results = (Category.query
                   .filter(Category.title_matches(q),
                           ~Category.is_deleted)
                   .options(undefer('chain'))
                   .order_by(db.func.lower(Category.title))
                   .paginate(page, RESULTS_PER_PAGE))
        # XXX should we only show categories the user can access?
        # this would be nicer but then we can't easily paginate...
        return {'results': CategoryResultSchema(many=True).dump(results.items),
                'page': results.page,
                'pages': results.pages,
                'total': results.total}


class RHSearchEvents(RH):
    @use_kwargs({
        'page': fields.Int(missing=1),
        'q': fields.String(required=True),
    })
    def _process(self, page, q):
        results = (Event.query
                   .filter(Event.title_matches(q),
                           Event.effective_protection_mode == ProtectionMode.public,
                           ~Event.is_deleted)
                   .order_by(db.func.lower(Event.title))
                   .paginate(page, RESULTS_PER_PAGE))
        # XXX should we only show categories the user can access?
        # this would be nicer but then we can't easily paginate...
        return {'results': EventResultSchema(many=True).dump(results.items),
                'page': results.page,
                'pages': results.pages,
                'total': results.total}
