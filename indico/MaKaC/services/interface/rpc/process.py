import time
import sys, traceback

from ZODB.POSException import ConflictError
from ZEO.Exceptions import ClientDisconnected

from MaKaC.webinterface import session
from MaKaC.services.interface import rpc
from MaKaC.services.interface.rpc import handlers
from MaKaC.plugins.base import Observable

from MaKaC.common import DBMgr, Config
from MaKaC.common.contextManager import ContextManager

from MaKaC.services.interface.rpc.common import CausedError
from MaKaC.services.interface.rpc.common import RequestError
from MaKaC.services.interface.rpc.common import ProcessError


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


def processRequest(method, params, req):
    # lookup handler
    handler = lookupHandler(method)

    # invoke handler
    if hasattr(handler, "process"):
        result = handler(params, getSession(req), req).process()
    else:
        result = handler(params, getSession(req), req)

    return result


class ServiceRunner(Observable):

    def invokeMethod(self, method, params, req):
        # create the context
        ContextManager.create()

        DBMgr.getInstance().startRequest()

        # room booking database
        _startRequestSpecific2RH()

        # notify components that the request has started
        self._notify('requestStarted', req)

        try:
            try:
                retry = 10
                while retry > 0:
                    if 10 - retry > 0:
                        # notify components that the request is being retried
                        self._notify('requestRetry', req, 10 - retry)

                    try:
                        DBMgr.getInstance().sync()

                        result = processRequest(method, params, req)

                        # notify components that the request has ended
                        self._notify('requestFinished', req)

                        _endRequestSpecific2RH( True )

                        DBMgr.getInstance().endRequest(True)
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
                        time.sleep(10 - retry)
                        continue
            except CausedError:
                raise
            except Exception, e:
                raise ProcessError("ERR-P0", "Error processing method.")
        finally:
            # destroy the context
            ContextManager.destroy()

    #    _endRequestSpecific2RH( False )

        return result

def getSession(req):
    sm = session.getSessionManager()
    try:
        websession = sm.get_session(req)
    except session.SessionError, e:
        sm.revoke_session_cookie(req)
        websession = sm.get_session(req)
    sm.maintain_session(req, websession)
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
