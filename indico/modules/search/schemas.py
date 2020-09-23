# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.marshmallow import mm
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.web.flask.util import url_for


def _get_category_path(chain):
    chain = chain[1:-1]  # strip root/self
    return [
        dict(c, url=url_for('categories.display', category_id=c['id']))
        for c in chain
    ]


class CategoryResultSchema(mm.ModelSchema):
    class Meta:
        model = Category
        fields = ('id', 'title', 'url', 'path')

    path = mm.Function(lambda cat: _get_category_path(cat.chain))


class EventResultSchema(mm.ModelSchema):
    class Meta:
        model = Event
        fields = ('id', 'title', 'url', 'type', 'start_dt', 'end_dt', 'category_path', 'speakers')

    category_path = mm.Function(lambda event: _get_category_path(event.detailed_category_chain))


class PersonSchema(mm.Schema):
    id = mm.Int()
    title = mm.String()
    name = mm.String()


class ContributionResultSchema(mm.Schema):
    id = mm.Int()
    title = mm.String()
    url = mm.String()
    start_dt = mm.String()
    eventURL = mm.String()
    eventTitle = mm.String()
    persons = mm.Nested(PersonSchema, many=True)


class FileResultSchema(mm.Schema):
    id = mm.Int()
    title = mm.String()
    url = mm.String()
    type = mm.String()
    contributionTitle = mm.String()
    date = mm.String()
    contribURL = mm.String()
    persons = mm.Nested(PersonSchema, many=True)
