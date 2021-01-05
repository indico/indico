# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import

from datetime import date, datetime
from UserDict import UserDict

from speaklater import _LazyString


try:
    import simplejson as _json
except ImportError:
    import json as _json


class IndicoJSONEncoder(_json.JSONEncoder):
    """Custom JSON encoder that supports more types.

     * datetime objects
    """
    def __init__(self, *args, **kwargs):
        if kwargs.get('separators') is None:
            kwargs['separators'] = (',', ':')
        super(IndicoJSONEncoder, self).__init__(*args, **kwargs)

    def default(self, o):
        if isinstance(o, _LazyString):
            return o.value
        elif isinstance(o, UserDict):
            return dict(o)
        elif isinstance(o, datetime):
            return {'date': str(o.date()), 'time': str(o.time()), 'tz': str(o.tzinfo)}
        elif isinstance(o, date):
            return str(o)
        return _json.JSONEncoder.default(self, o)


def dumps(obj, **kwargs):
    """Simple wrapper around json.dumps()."""
    if kwargs.pop('pretty', False):
        kwargs['indent'] = 4 * ' '
    textarea = kwargs.pop('textarea', False)
    ret = _json.dumps(obj, cls=IndicoJSONEncoder, **kwargs).replace('/', '\\/')

    if textarea:
        return '<html><head></head><body><textarea>%s</textarea></body></html>' % ret
    else:
        return ret


def loads(string):
    """Simple wrapper around json.decode()."""
    return _json.loads(string)
