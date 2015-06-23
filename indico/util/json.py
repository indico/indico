# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

import traceback
from datetime import datetime, date

from flask import current_app
from persistent.dict import PersistentDict
from speaklater import _LazyString

from indico.core.config import Config
from indico.core.errors import IndicoError

try:
    import simplejson as _json
except ImportError:
    import json as _json


class IndicoJSONEncoder(_json.JSONEncoder):
    """
    Custom JSON encoder that supports more types
     * datetime objects
     * PersistentDict
    """
    def default(self, o):
        if isinstance(o, _LazyString):
            return o.value
        elif isinstance(o, PersistentDict):
            return dict(o)
        elif isinstance(o, datetime):
            return {'date': str(o.date()), 'time': str(o.time()), 'tz': str(o.tzinfo)}
        elif isinstance(o, date):
            return str(o)
        return _json.JSONEncoder.default(self, o)


def dumps(obj, **kwargs):
    """
    Simple wrapper around json.dumps()
    """
    if kwargs.pop('pretty', False):
        kwargs['indent'] = 4 * ' '
    textarea = kwargs.pop('textarea', False)
    ret = _json.dumps(obj, cls=IndicoJSONEncoder, **kwargs).replace('/', '\\/')

    if textarea:
        return '<html><head></head><body><textarea>%s</textarea></body></html>' % ret
    else:
        return ret


def loads(string):
    """
    Simple wrapper around json.decode()
    """
    return _json.loads(string)


def create_json_error_answer(exception, status=200):
    if isinstance(exception, IndicoError):
        details = exception.toDict()
    else:
        exception_data = exception.__dict__
        try:
            _json.dumps(exception_data)
        except Exception:
            exception_data = {}
        details = {
            'code': type(exception).__name__,
            'type': 'unknown',
            # werkzeug HTTPExceptions have a description instead of a message.
            'message': unicode(getattr(exception, 'description', exception.message)),
            'data': exception_data,
            'requestInfo': {},
            'inner': traceback.format_exc()
        }

    return current_app.response_class(dumps({
        'version': Config.getInstance().getVersion(),
        'result': None,
        'error': details
    }), mimetype='application/json', status=status)
