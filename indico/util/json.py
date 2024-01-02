# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import annotations

import typing as t
from collections import UserDict
from datetime import date, datetime

import simplejson
from flask.json.provider import JSONProvider
from speaklater import _LazyString


class IndicoJSONEncoder(simplejson.JSONEncoder):
    """Custom JSON encoder that supports more types."""

    def __init__(self, *args, **kwargs):
        if kwargs.get('separators') is None:
            kwargs['separators'] = (',', ':')
        super().__init__(*args, **kwargs)

    def default(self, o):
        if isinstance(o, _LazyString):
            return o.value
        elif isinstance(o, UserDict):
            return dict(o)
        elif isinstance(o, datetime):
            return {'date': str(o.date()), 'time': str(o.time()), 'tz': str(o.tzinfo)}
        elif isinstance(o, date):
            return str(o)
        return simplejson.JSONEncoder.default(self, o)


class IndicoJSONProvider(JSONProvider):
    def dumps(self, obj: t.Any, **kwargs: t.Any) -> str:
        kwargs.setdefault('cls', IndicoJSONEncoder)
        kwargs.setdefault('sort_keys', True)  # XXX not sure if we need it, but it was on before
        return simplejson.dumps(obj, **kwargs)

    def loads(self, s: str | bytes, **kwargs: t.Any) -> t.Any:
        return simplejson.loads(s, **kwargs)

    def _prepare_response_obj(self, args: tuple[t.Any, ...], kwargs: dict[str, t.Any]) -> t.Any:
        if not args and not kwargs:
            return {}
        return super()._prepare_response_obj(args, kwargs)
