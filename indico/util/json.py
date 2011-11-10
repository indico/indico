# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

try:
    import simplejson as _json
except ImportError:
    import json as _json

from persistent.dict import PersistentDict
from datetime import datetime
from indico.util.i18n import LazyProxy

# Test if simplejson escapes forward slashes. It changed its behaviour im some version.
if '\\/' in _json.dumps('/'):
    _json_dumps = simplejson.dumps
else:
    def _json_dumps(*args, **kwargs):
        return _json.dumps(*args, **kwargs).replace('/', '\\/')

class _JSONEncoder(_json.JSONEncoder):
    """
    Custom JSON encoder that supports more types
     * datetime objects
     * PersistentDict
    """
    def default(self, o):
        if isinstance(o, LazyProxy):
            return str(o)
        elif isinstance(o, PersistentDict):
            return dict(o)
        elif type(o) is datetime:
            return {'date': str(o.date()), 'time': str(o.time()), 'tz': str(o.tzinfo)}
        return _json.JSONEncoder.default(self, o)


def dumps(obj, **kwargs):
    """
    Simple wrapper around json.dumps()
    """
    if kwargs.pop('pretty', False):
        kwargs['indent'] = 4 * ' '
    textarea = kwargs.pop('textarea', False)
    ret = _json_dumps(obj, cls=_JSONEncoder, **kwargs)
    if textarea:
        return '<html><head></head><body><textarea>%s</textarea></body></html>' % ret
    else:
        return ret



def loads(string):
    """
    Simple wrapper around json.decode()
    """
    return _json.loads(string)


def json_filter(obj):
    """
    Mako filter
    """
    return _json_dumps(obj)
