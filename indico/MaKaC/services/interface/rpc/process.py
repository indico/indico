import time
import sys, traceback

from ZODB.POSException import ConflictError
from ZEO.Exceptions import ClientDisconnected

from MaKaC.webinterface import session
from MaKaC.services.interface import rpc
from MaKaC.services.interface.rpc import handlers

from MaKaC.common import DBMgr, Config
from MaKaC.common.contextManager import ContextManager

from MaKaC.services.interface.rpc.common import CausedError
from MaKaC.services.interface.rpc.common import RequestError
from MaKaC.services.interface.rpc.common import ProcessError

def lookupHandler(method):
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
        result = handler(params, req.get_remote_host(), getSession(req)).process()
    else:
        result = handler(params, req.get_remote_host(), getSession(req))

    return result

def invokeMethod(method, params, req):

    # create the context
    ContextManager.create()

    DBMgr.getInstance().startRequest()

    # room booking database
    _startRequestSpecific2RH()
    try:
        try:
            retry = 10
            while retry > 0:
                try:
                    DBMgr.getInstance().sync()

                    result = processRequest(method, params, req)

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
        except CausedError, e:
            raise e
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
