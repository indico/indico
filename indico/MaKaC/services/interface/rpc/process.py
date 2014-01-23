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
from flask import request, session

import time
import sys, traceback
import copy

from ZODB.POSException import ConflictError
from ZEO.Exceptions import ClientDisconnected
from MaKaC.common.logger import Logger

from MaKaC.services.interface import rpc
from MaKaC.services.interface.rpc import handlers
from MaKaC.plugins.base import Observable
import MaKaC.errors

from indico.core.db import DBMgr
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.mail import GenericMailer

from MaKaC.services.interface.rpc.common import CausedError, NoReportError, CSRFError
from MaKaC.services.interface.rpc.common import RequestError
from MaKaC.services.interface.rpc.common import ProcessError

from indico.util.redis import RedisError
from indico.util import fossilize
from indico.core.config import Config


def lookupHandler(method):
    # TODO: better way to do this without the need of DB connection?
    handlers.updateMethodMapWithPlugins()

    endpoint = handlers
    functionName = method
    while True:
        handler = endpoint.methodMap.get(functionName, None)
        if handler != None:
            break
        try:
            endpointName, functionName = method.split(".", 1)
        except:
            raise RequestError("ERR-R1", "Unsupported method.")

        if 'endpointMap' in dir(endpoint):
            endpoint = endpoint.endpointMap.get(endpointName, None)
            if endpoint == None:
                raise RequestError("ERR-R0", "Unknown endpoint: %s" % endpointName)
        else:
            raise RequestError("ERR-R1", "Unsupported method")
    return handler


def processRequest(method, params, internal=False):
    # lookup handler
    handler = lookupHandler(method)

    if not internal and Config.getInstance().getCSRFLevel() >= 1:
        if session.csrf_protected and session.csrf_token != request.headers.get('X-CSRF-Token'):
            raise CSRFError()

    # invoke handler
    if hasattr(handler, "process"):
        result = handler(params).process()
    else:
        result = handler(params)

    return result


class ServiceRunner(Observable):

    def invokeMethod(self, method, params):

        MAX_RETRIES = 10

        # clear the context
        ContextManager.destroy()

        DBMgr.getInstance().startRequest()

        # room booking database
        _startRequestSpecific2RH()

        # notify components that the request has started
        self._notify('requestStarted')

        forcedConflicts = Config.getInstance().getForceConflicts()
        retry = MAX_RETRIES
        try:
            while retry > 0:
                if retry < MAX_RETRIES:
                    # notify components that the request is being retried
                    self._notify('requestRetry', MAX_RETRIES - retry)

                # clear/init fossil cache
                fossilize.clearCache()

                try:
                    # delete all queued emails
                    GenericMailer.flushQueue(False)

                    DBMgr.getInstance().sync()

                    try:
                        result = processRequest(method, copy.deepcopy(params))
                    except MaKaC.errors.NoReportError, e:
                        raise NoReportError(e.getMessage())
                    rh = ContextManager.get('currentRH')

                    # notify components that the request has ended
                    self._notify('requestFinished')
                    # Raise a conflict error if enabled. This allows detecting conflict-related issues easily.
                    if retry > (MAX_RETRIES - forcedConflicts):
                        raise ConflictError
                    _endRequestSpecific2RH( True )
                    DBMgr.getInstance().endRequest(True)
                    GenericMailer.flushQueue(True) # send emails
                    if rh._redisPipeline:
                        try:
                            rh._redisPipeline.execute()
                        except RedisError:
                            Logger.get('redis').exception('Could not execute pipeline')
                    break
                except ConflictError:
                    _abortSpecific2RH()
                    DBMgr.getInstance().abort()
                    retry -= 1
                    continue
                except ClientDisconnected:
                    _abortSpecific2RH()
                    DBMgr.getInstance().abort()
                    retry -= 1
                    time.sleep(MAX_RETRIES - retry)
                    continue
        except CausedError:
            _endRequestSpecific2RH(False)
            DBMgr.getInstance().endRequest(False)
            raise
        except Exception:
            _endRequestSpecific2RH(False)
            DBMgr.getInstance().endRequest(False)
            raise ProcessError("ERR-P0", "Error processing method.")

        return result

from MaKaC.rb_location import CrossLocationDB
import MaKaC.common.info as info


def _startRequestSpecific2RH():
    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
    if minfo.getRoomBookingModuleActive():
        CrossLocationDB.connect()

def _endRequestSpecific2RH(commit=True):
    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
    if minfo.getRoomBookingModuleActive():
        if commit:
            CrossLocationDB.commit()
        else:
            CrossLocationDB.rollback()
        CrossLocationDB.disconnect()

def _syncSpecific2RH():
    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
    if minfo.getRoomBookingModuleActive():
        CrossLocationDB.sync()

def _abortSpecific2RH():
    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
    if minfo.getRoomBookingModuleActive():
        CrossLocationDB.rollback()
