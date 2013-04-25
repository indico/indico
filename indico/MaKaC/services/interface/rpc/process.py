# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

import time
import sys, traceback

from ZODB.POSException import ConflictError
from ZEO.Exceptions import ClientDisconnected

from MaKaC.webinterface import session
from MaKaC.services.interface import rpc
from MaKaC.services.interface.rpc import handlers
from MaKaC.plugins.base import Observable
import MaKaC.errors

from MaKaC.common import DBMgr, Config
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.mail import GenericMailer

from MaKaC.services.interface.rpc.common import CausedError, NoReportError
from MaKaC.services.interface.rpc.common import RequestError
from MaKaC.services.interface.rpc.common import ProcessError

import copy


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


def processRequest(method, params, req, internal=False):
    # lookup handler
    handler = lookupHandler(method)
    websession = getSession(req)

    if not internal and Config.getInstance().getCSRFLevel() >= 1:
        if websession.csrf_protected and websession.csrf_token != req.headers_in.get('X-CSRF-Token'):
            raise RequestError('ERR-R4', _('Invalid CSRF token'))

    # invoke handler
    if hasattr(handler, "process"):
        result = handler(params, websession, req).process()
    else:
        result = handler(params, websession, req)

    # commit session if necessary
    session.getSessionManager().maintain_session(req, websession)

    return result


class ServiceRunner(Observable):

    def invokeMethod(self, method, params, req):

        MAX_RETRIES = 10

        # clear the context
        ContextManager.destroy()

        DBMgr.getInstance().startRequest()

        # room booking database
        _startRequestSpecific2RH()

        # notify components that the request has started
        self._notify('requestStarted', req)

        forcedConflicts = Config.getInstance().getForceConflicts()
        retry = MAX_RETRIES
        try:
            while retry > 0:
                if retry < MAX_RETRIES:
                    # notify components that the request is being retried
                    self._notify('requestRetry', req, MAX_RETRIES - retry)

                try:
                    # delete all queued emails
                    GenericMailer.flushQueue(False)

                    DBMgr.getInstance().sync()

                    try:
                        result = processRequest(method, copy.deepcopy(params), req)
                    except MaKaC.errors.NoReportError, e:
                        raise NoReportError(e.getMsg())
                    rh = ContextManager.get('currentRH')

                    # notify components that the request has ended
                    self._notify('requestFinished', req)
                    # Raise a conflict error if enabled. This allows detecting conflict-related issues easily.
                    if retry > (MAX_RETRIES - forcedConflicts):
                        raise ConflictError
                    _endRequestSpecific2RH( True )
                    DBMgr.getInstance().endRequest(True)
                    GenericMailer.flushQueue(True) # send emails
                    if rh._redisPipeline:
                        rh._redisPipeline.execute()
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
            raise
        except Exception:
            raise ProcessError("ERR-P0", "Error processing method.")

        return result

def getSession(req):
    sm = session.getSessionManager()
    try:
        websession = sm.get_session(req)
    except session.SessionError:
        sm.revoke_session_cookie(req)
        websession = sm.get_session(req)
    return websession

from MaKaC.rb_location import CrossLocationDB
import MaKaC.common.info as info

def _startRequestSpecific2RH():
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getRoomBookingModuleActive():
            CrossLocationDB.connect()

def _endRequestSpecific2RH( commit = True ):
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
