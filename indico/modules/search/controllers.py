# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import division, unicode_literals

from datetime import datetime
from math import ceil

import pytz
from marshmallow import fields
from sqlalchemy.orm import undefer

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.search.schemas import (CategoryResultSchema, ContributionResultSchema, EventResultSchema,
                                           FileResultSchema)
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


class RHSearchContributions(RH):
    @use_kwargs({
        'page': fields.Int(missing=1),
        'q': fields.String(required=True),
    })
    def _process(self, page, q):
        data = [x for x in CONTRIB_DATA if q.lower() in x['title'].lower()]
        total = len(data)
        offset = (page - 1) * RESULTS_PER_PAGE
        items = data[offset:offset + RESULTS_PER_PAGE]
        pages = int(ceil(total / RESULTS_PER_PAGE))
        return {'results': ContributionResultSchema(many=True).dump(items),
                'page': page,
                'pages': pages,
                'total': total}


class RHSearchFiles(RH):
    @use_kwargs({
        'page': fields.Int(missing=1),
        'q': fields.String(required=True),
    })
    def _process(self, page, q):
        data = [x for x in FILE_DATA if q.lower() in x['title'].lower()]
        total = len(data)
        offset = (page - 1) * RESULTS_PER_PAGE
        items = data[offset:offset + RESULTS_PER_PAGE]
        pages = int(ceil(total / RESULTS_PER_PAGE))
        return {'results': FileResultSchema(many=True).dump(items),
                'page': page,
                'pages': pages,
                'total': total}


# dummy data
CONTRIB_DATA = [
    {'id': 2703412,
     'persons': [{'id': 3319533, 'name': u'Michal Kolodziejski', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 18, 13, 0)),
     'title': u'Enterprise Authentication with Indico'},
    {'id': 2703405,
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'persons': [{'id': 3336048, 'name': u'Dirk Hoffmann', 'title': u'Dr'}],
     'start_dt': pytz.utc.localize(datetime(2017, 10, 19, 9, 0)),
     'title': u'Internationalization - tips and tricks'},
    {'id': 2703418,
     'persons': [{'id': 3319501, 'name': u'Pedro Ferreira', 'title': u''},
                 {'id': 3361462, 'name': u'Thomas Baron', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 18, 7, 50)),
     'title': u"What's new in the Indicoverse?"},
    {'id': 2703408,
     'persons': [{'id': 3319509, 'name': u'Natalia Karina Juszka', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 19, 7, 0)),
     'title': u'Any colour you like - customising Indico'},
    {'id': 2703430,
     'persons': [{'id': 3319550, 'name': u'Adrian M\xf6nnich', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 20, 7, 15)),
     'title': u'Maintaining an Indico instance - tips and tricks'},
    {'id': 2703409,
     'persons': [{'id': 3319523, 'name': u'Adrian M\xf6nnich', 'title': u''},
                 {'id': 3319524, 'name': u'Natalia Karina Juszka', 'title': u''},
                 {'id': 3319525, 'name': u'Pedro Ferreira', 'title': u''},
                 {'id': 3319526, 'name': u'Marco Vidal', 'title': u''},
                 {'id': 3319527, 'name': u'Michal Kolodziejski', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 18, 14, 0)),
     'title': u'Indico Development Bootcamp'},
    {'id': 2703410,
     'persons': [{'id': 3319506, 'name': u'Natalia Karina Juszka', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 20, 9, 0)),
     'title': u'Walkthrough - Developing a Plugin'},
    {'id': 2703425,
     'persons': [{'id': 3377568, 'name': u'Pedro Ferreira', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 20, 12, 30)),
     'title': u'The Future'},
    {'id': 2703398,
     'persons': [{'id': 3368725, 'name': u'Adrian M\xf6nnich', 'title': u''},
                 {'id': 3368726, 'name': u'Pedro Ferreira', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 18, 8, 50)),
     'title': u"Version 2.0 - What's new?"},
    {'id': 2703400,
     'persons': [{'id': 3319499, 'name': u'Adrian M\xf6nnich', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 18, 9, 50)),
     'title': u'Version 2.0 - Under the hood'},
    {'id': 2703414,
     'persons': [{'id': 3328200, 'name': u'Stefan Hesselbach', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 18, 12, 0)),
     'title': u'Indico @ GSI'},
    {'id': 2703415,
     'persons': [{'id': 3328767, 'name': u'Giorgio Pieretti', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 19, 9, 30)),
     'title': u'Indico @ UNOG'},
    {'id': 2703413,
     'persons': [{'id': 3319503, 'name': u'Marco Vidal', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 19, 7, 30)),
     'title': u'Walkthrough: Container Deployment'},
    {'id': 2703416,
     'persons': [{'id': 3362150, 'name': u'Akihiro Shibata', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 20, 8, 15)),
     'title': u'Indico @ KEK'},
    {'id': 2703417,
     'persons': [{'id': 3367992, 'name': u'Thomas Baron', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 18, 7, 30)),
     'title': u'Welcome to CERN'},
    {'id': 2703402,
     'persons': [{'id': 3319515, 'name': u'Pedro Ferreira', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 18, 12, 15)),
     'title': u'Walkthrough - Migrating to 2.0'},
    {'id': 2703681,
     'persons': [{'id': 3319528, 'name': u'Pedro Ferreira', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 20, 7, 0)),
     'title': u'The Big Migration: An overview of three years of development'},
    {'id': 2703772,
     'persons': [{'id': 3328765, 'name': u'Penelope Constanta', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 19, 8, 45)),
     'title': u'Indico @ Fermilab'},
    {'id': 2703808,
     'persons': [{'id': 3377569, 'name': u'Thomas Baron', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 20, 13, 0)),
     'title': u'Wrap-up'},
    {'id': 2703807,
     'persons': [{'id': 3379616, 'name': u'Natalia Karina Juszka', 'title': u''},
                 {'id': 3379617, 'name': u'Pedro Ferreira', 'title': u''},
                 {'id': 3379618, 'name': u'Michal Kolodziejski', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 20, 11, 30)),
     'title': u'Brainstorming: Event-based collaboration'},
    {'id': 2704040,
     'persons': [{'id': 3319540, 'name': u'Marco Vidal', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 20, 7, 45)),
     'title': u'Indico Community - Bringing everyone together'},
    {'id': 2754586,
     'persons': [{'id': 3367991, 'name': u'Tim Smith', 'title': u''}],
     'url': '/category/1',
     'eventURL': '/event/741230/',
     'eventTitle': '"This is the event Title"',
     'start_dt': pytz.utc.localize(datetime(2017, 10, 18, 7, 40)),
     'title': u'CERN and Indico'}
]

FILE_DATA = [
    {'id': 2703412,
     'persons': [],
     'url': '/category/1',
     'type': 'file-word',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 18, 13, 0)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Enterprise Authentication with Indico'},
    {'id': 2703405,
     'url': '/category/1',
     'type': 'file-presentation',
     'contributionTitle': '"A contribution title goes here"',
     'persons': [{'id': 3336048, 'name': u'Dirk Hoffmann', 'title': u'Dr'}],
     'date': pytz.utc.localize(datetime(2017, 10, 19, 9, 0)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Internationalization - tips and tricks'},
    {'id': 2703418,
     'persons': [{'id': 3319501, 'name': u'Pedro Ferreira', 'title': u''},
                 {'id': 3361462, 'name': u'Thomas Baron', 'title': u''}],
     'url': '/category/1',
     'type': 'file-excel',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 18, 7, 50)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u"What's new in the Indicoverse?"},
    {'id': 2703408,
     'persons': [{'id': 3319509, 'name': u'Natalia Karina Juszka', 'title': u''}],
     'url': '/category/1',
     'type': 'file-zip',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 19, 7, 0)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Any colour you like - customising Indico'},
    {'id': 2703430,
     'persons': [{'id': 3319550, 'name': u'Adrian M\xf6nnich', 'title': u''}],
     'url': '/category/1',
     'type': 'file-xml',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 20, 7, 15)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Maintaining an Indico instance - tips and tricks'},
    {'id': 2703409,
     'persons': [{'id': 3319523, 'name': u'Adrian M\xf6nnich', 'title': u''},
                 {'id': 3319524, 'name': u'Natalia Karina Juszka', 'title': u''},
                 {'id': 3319525, 'name': u'Pedro Ferreira', 'title': u''},
                 {'id': 3319526, 'name': u'Marco Vidal', 'title': u''},
                 {'id': 3319527, 'name': u'Michal Kolodziejski', 'title': u''}],
     'url': '/category/1',
     'type': 'file-spreadsheet',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 18, 14, 0)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Indico Development Bootcamp'},
    {'id': 2703410,
     'persons': [{'id': 3319506, 'name': u'Natalia Karina Juszka', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 20, 9, 0)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Walkthrough - Developing a Plugin'},
    {'id': 2703425,
     'persons': [{'id': 3377568, 'name': u'Pedro Ferreira', 'title': u''}],
     'url': '/category/1',
     'type': 'file',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 20, 12, 30)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'The Future'},
    {'id': 2703398,
     'persons': [{'id': 3368725, 'name': u'Adrian M\xf6nnich', 'title': u''},
                 {'id': 3368726, 'name': u'Pedro Ferreira', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 18, 8, 50)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u"Version 2.0 - What's new?"},
    {'id': 2703400,
     'persons': [{'id': 3319499, 'name': u'Adrian M\xf6nnich', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 18, 9, 50)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Version 2.0 - Under the hood'},
    {'id': 2703414,
     'persons': [{'id': 3328200, 'name': u'Stefan Hesselbach', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 18, 12, 0)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Indico @ GSI'},
    {'id': 2703415,
     'persons': [{'id': 3328767, 'name': u'Giorgio Pieretti', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 19, 9, 30)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Indico @ UNOG'},
    {'id': 2703413,
     'persons': [{'id': 3319503, 'name': u'Marco Vidal', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 19, 7, 30)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Walkthrough: Container Deployment'},
    {'id': 2703416,
     'persons': [{'id': 3362150, 'name': u'Akihiro Shibata', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 20, 8, 15)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Indico @ KEK'},
    {'id': 2703417,
     'persons': [{'id': 3367992, 'name': u'Thomas Baron', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 18, 7, 30)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Welcome to CERN'},
    {'id': 2703402,
     'persons': [{'id': 3319515, 'name': u'Pedro Ferreira', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 18, 12, 15)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Walkthrough - Migrating to 2.0'},
    {'id': 2703681,
     'persons': [{'id': 3319528, 'name': u'Pedro Ferreira', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 20, 7, 0)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'The Big Migration: An overview of three years of development'},
    {'id': 2703772,
     'persons': [{'id': 3328765, 'name': u'Penelope Constanta', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 19, 8, 45)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Indico @ Fermilab'},
    {'id': 2703808,
     'persons': [{'id': 3377569, 'name': u'Thomas Baron', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 20, 13, 0)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Wrap-up'},
    {'id': 2703807,
     'persons': [{'id': 3379616, 'name': u'Natalia Karina Juszka', 'title': u''},
                 {'id': 3379617, 'name': u'Pedro Ferreira', 'title': u''},
                 {'id': 3379618, 'name': u'Michal Kolodziejski', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 20, 11, 30)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Brainstorming: Event-based collaboration'},
    {'id': 2704040,
     'persons': [{'id': 3319540, 'name': u'Marco Vidal', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 20, 7, 45)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'Indico Community - Bringing everyone together'},
    {'id': 2754586,
     'persons': [{'id': 3367991, 'name': u'Tim Smith', 'title': u''}],
     'url': '/category/1',
     'type': 'file-pdf',
     'contributionTitle': '"A contribution title goes here"',
     'date': pytz.utc.localize(datetime(2017, 10, 18, 7, 40)),
     'contribURL': '/event/136179/contributions/6/',
     'title': u'CERN and Indico'}
]
