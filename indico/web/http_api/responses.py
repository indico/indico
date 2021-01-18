# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import time

from marshmallow import fields
from marshmallow.decorators import post_dump

from indico.core.config import config
from indico.core.marshmallow import mm


class HTTPAPIError(Exception):
    def __init__(self, message, code=None):
        self.message = message
        self.code = code


class HTTPAPIResult:
    def __init__(self, results, path='', query='', ts=None, extra=None):
        if ts is None:
            ts = int(time.time())
        self.results = results
        self.path = path
        self.query = query
        self.ts = ts
        self.extra = extra or {}

    @property
    def url(self):
        prefix = config.BASE_URL
        if self.query:
            return f'{prefix}{self.path}?{self.query}'
        return prefix + self.path

    @property
    def count(self):
        return len(self.results)


class HTTPAPIResultSchema(mm.Schema):
    count = fields.Integer()
    extra = fields.Raw(data_key='additionalInfo')
    ts = fields.Integer()
    url = fields.String()
    results = fields.Raw()

    @post_dump
    def _add_type(self, data, **kwargs):
        data['_type'] = 'HTTPAPIResult'
        return data
