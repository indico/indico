# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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
from UserDict import UserDict

from flask import current_app, session
from speaklater import _LazyString
from werkzeug.exceptions import Forbidden

from indico.web.util import get_request_info

try:
    import simplejson as _json
except ImportError:
    import json as _json


class IndicoJSONEncoder(_json.JSONEncoder):
    """
    Custom JSON encoder that supports more types
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


def _is_no_report_error(exc):
    from indico.core import errors as indico_errors
    from indico.legacy import errors as makac_errors
    return (isinstance(exc, (indico_errors.NoReportError, makac_errors.NoReportError)) or
            getattr(exc, '_disallow_report', False))


def create_json_error_answer(exception, status=200):
    from indico.core.config import Config
    from indico.core.errors import IndicoError, get_error_description
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
            'hasUser': bool(session.user),
            'type': 'noReport' if ((not session.user and isinstance(exception, Forbidden)) or
                                   _is_no_report_error(exception)) else 'unknown',
            'message': unicode(get_error_description(exception)),
            'data': exception_data,
            'requestInfo': get_request_info(),
            'inner': traceback.format_exc()
        }

    return current_app.response_class(dumps({
        'version': Config.getInstance().getVersion(),
        'result': None,
        'error': details
    }), mimetype='application/json', status=status)
