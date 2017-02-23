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

import copy
import sys

import transaction
from flask import request, session
from sqlalchemy.exc import DatabaseError

from MaKaC.errors import NoReportError, FormValuesError
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.mail import GenericMailer
from MaKaC.services.interface.rpc import handlers
from MaKaC.services.interface.rpc.common import (CausedError,
                                                 CSRFError,
                                                 NoReportError as ServiceNoReportError)
from MaKaC.services.interface.rpc.common import RequestError
from MaKaC.services.interface.rpc.common import ProcessError
from indico.core import signals
from indico.core.config import Config
from indico.core.db.sqlalchemy.core import handle_sqlalchemy_database_error, ConstraintViolated
from indico.core.errors import NoReportError as NoReportIndicoError
from indico.util import fossilize


def lookupHandler(method):
    endpoint, functionName = handlers, method
    while True:
        handler = endpoint.methodMap.get(functionName, None)
        if handler:
            break
        try:
            endpointName, functionName = method.split('.', 1)
        except Exception:
            raise RequestError('ERR-R1', 'Unsupported method.')

        if 'endpointMap' in dir(endpoint):
            endpoint = endpoint.endpointMap.get(endpointName, None)
            if not endpoint:
                raise RequestError('ERR-R0', 'Unknown endpoint: {0}'.format(endpointName))
        else:
            raise RequestError('ERR-R1', 'Unsupported method')
    return handler


def processRequest(method, params, internal=False):
    # lookup handler
    handler = lookupHandler(method)

    if not internal and Config.getInstance().getCSRFLevel() >= 1:
        if session.csrf_protected and session.csrf_token != request.headers.get('X-CSRF-Token'):
            raise CSRFError()

    # invoke handler
    if hasattr(handler, 'process'):
        result = handler(params).process()
    else:
        result = handler(params)

    return result


class ServiceRunner(object):
    def invokeMethod(self, method, params):
        result = None

        try:
            ContextManager.destroy()
            fossilize.clearCache()
            GenericMailer.flushQueue(False)
            try:
                try:
                    result = processRequest(method, copy.deepcopy(params))
                    signals.after_process.send()
                except NoReportError as e:
                    raise ServiceNoReportError(e.getMessage())
                except (NoReportIndicoError, FormValuesError) as e:
                    raise ServiceNoReportError(e.getMessage(), title=_("Error"))
                transaction.commit()
            except DatabaseError:
                handle_sqlalchemy_database_error()
            GenericMailer.flushQueue(True)
        except Exception as e:
            transaction.abort()
            if isinstance(e, CausedError):
                raise
            elif isinstance(e, ConstraintViolated):
                raise ProcessError, ('ERR-P0', e.message), sys.exc_info()[2]
            else:
                raise ProcessError('ERR-P0', 'Error processing method.')

        return result
