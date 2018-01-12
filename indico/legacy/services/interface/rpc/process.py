# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import copy

from flask import request, session
from sqlalchemy.exc import DatabaseError
from werkzeug.exceptions import BadRequest

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.core import handle_sqlalchemy_database_error
from indico.core.notifications import flush_email_queue, init_email_queue
from indico.legacy.services.interface.rpc import handlers
from indico.util import fossilize


def _lookup_handler(method):
    endpoint, functionName = handlers, method
    while True:
        handler = endpoint.methodMap.get(functionName, None)
        if handler:
            break
        try:
            endpointName, functionName = method.split('.', 1)
        except Exception:
            raise BadRequest('Unsupported method')

        if 'endpointMap' in dir(endpoint):
            endpoint = endpoint.endpointMap.get(endpointName, None)
            if not endpoint:
                raise BadRequest('Unknown endpoint: {}'.format(endpointName))
        else:
            raise BadRequest('Unsupported method')
    return handler


def _process_request(method, params):
    handler = _lookup_handler(method)

    if session.csrf_protected and session.csrf_token != request.headers.get('X-CSRF-Token'):
        msg = _(u"It looks like there was a problem with your current session. Please use your browser's back "
                u"button, reload the page and try again.")
        raise BadRequest(msg)

    if hasattr(handler, 'process'):
        return handler(params).process()
    else:
        return handler(params)


def invoke_method(method, params):
    result = None
    fossilize.clearCache()
    init_email_queue()
    try:
        result = _process_request(method, copy.deepcopy(params))
        signals.after_process.send()
        db.session.commit()
    except DatabaseError:
        db.session.rollback()
        handle_sqlalchemy_database_error()
    except Exception:
        db.session.rollback()
        raise
    flush_email_queue()
    return result
