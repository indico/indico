# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import copy
import time

import transaction
from flask import request, session
from ZODB.POSException import ConflictError
from ZEO.Exceptions import ClientDisconnected

from MaKaC.plugins.base import Observable
from MaKaC.errors import NoReportError
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.mail import GenericMailer
from MaKaC.services.interface.rpc import handlers
from MaKaC.services.interface.rpc.common import(
    CausedError,
    NoReportError as ServiceNoReportError,
    CSRFError
)
from MaKaC.services.interface.rpc.common import RequestError
from MaKaC.services.interface.rpc.common import ProcessError

from indico.core.config import Config
from indico.core.db import DBMgr
from indico.core.logger import Logger
from indico.core.errors import NoReportError as NoReportIndicoError
from indico.util.redis import RedisError
from indico.util import fossilize


def lookupHandler(method):
    # TODO: better way to do this without the need of DB connection?
    handlers.updateMethodMapWithPlugins()

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


class ServiceRunner(Observable):

    def _invokeMethodBefore(self):
        # clear the context
        ContextManager.destroy()
        # notify components that the request has started
        DBMgr.getInstance().startRequest()
        self._notify('requestStarted')

    def _invokeMethodRetryBefore(self):
        # clear/init fossil cache
        fossilize.clearCache()
        # delete all queued emails
        GenericMailer.flushQueue(False)
        DBMgr.getInstance().sync()

    def _invokeMethodSuccess(self):
        rh = ContextManager.get('currentRH')

        GenericMailer.flushQueue(True) # send emails
        if rh._redisPipeline:
            try:
                rh._redisPipeline.execute()
            except RedisError:
                Logger.get('redis').exception('Could not execute pipeline')

    def invokeMethod(self, method, params):
        cfg = Config.getInstance()
        forced_conflicts, max_retries = cfg.getForceConflicts(), cfg.getMaxRetries()
        result = None

        self._invokeMethodBefore()

        try:
            for i, retry in enumerate(transaction.attempts(max_retries)):
                with retry:
                    if i > 0:
                        # notify components that the request is being retried
                        self._notify('requestRetry', i)

                    self._invokeMethodRetryBefore()
                    try:
                        # Raise a conflict error if enabled.
                        # This allows detecting conflict-related issues easily.
                        if i < forced_conflicts:
                            raise ConflictError
                        try:
                            result = processRequest(method, copy.deepcopy(params))
                        except NoReportError as e:
                            raise ServiceNoReportError(e.getMsg())
                        except NoReportIndicoError as e:
                            raise ServiceNoReportError(e.getMessage())

                        transaction.commit()
                        break
                    except ConflictError:
                        transaction.abort()
                    except ClientDisconnected:
                        transaction.abort()
                        time.sleep(i)
            self._invokeMethodSuccess()
        except Exception as e:
            transaction.abort()
            if isinstance(e, CausedError):
                raise
            raise ProcessError('ERR-P0', 'Error processing method.')
        finally:
            # notify components that the request has ended
            self._notify('requestFinished')
            DBMgr.getInstance().endRequest()

        return result
