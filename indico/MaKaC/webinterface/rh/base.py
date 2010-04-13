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
from MaKaC.webinterface.pages.conferences import WPConferenceModificationClosed
from MaKaC.common.TemplateExec import escapeHTMLForJS

"""Base definitions for the request handlers (rh). A rh is a class which
complies to a well defined interface and which from a mod_python request knows
which action to carry out in order to handle the request made. This means that
each of the possible HTTP ports of the system will have a rh which will know
what to do depending on the parameter values received, etc.
"""
import copy, time, os, sys, random, re
import StringIO
from datetime import datetime, timedelta

try:
    from mod_python.util import Field
    from mod_python import apache
except ImportError:
    pass
from ZODB.POSException import ConflictError
from ZEO.Exceptions import ClientDisconnected

import MaKaC.webinterface.session as session
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.errors as errors
from MaKaC.common.general import *

from MaKaC.accessControl import AccessWrapper
from MaKaC.common import DBMgr, Config, security
from MaKaC.errors import MaKaCError, ModificationError, AccessError, TimingError, ParentTimingError, EntryTimingError, FormValuesError, NoReportError, htmlScriptError, htmlForbiddenTag, ConferenceClosedError, HostnameResolveError
from MaKaC.webinterface.mail import GenericMailer, GenericNotification
from xml.sax.saxutils import escape

from MaKaC.common.utils import truncate
from MaKaC.common.logger import Logger
from MaKaC.common.contextManager import ContextManager
from MaKaC.i18n import _

from MaKaC.common.contextManager import ContextManager
from MaKaC.i18n import _

from MaKaC.common.TemplateExec import escapeHTMLForJS

class RequestHandlerBase(object):

    _uh = None

    def _checkProtection( self ):
        """
        """
        pass

    def getAW( self ):
        """
        Returns the access wrapper related to this session/user
        """
        return self._aw

    def _getUser(self):
        """
        Returns the current user
        """
        return self._aw.getUser()

    def _setUser(self, newUser=None):
        """
        Sets the current user
        """
        self._aw.setUser(newUser)

    def getCurrentURL( self ):
        """
        Gets the "current URL", through the URL handler
        """
        if self._uh == None:
            return ""
        return self._uh.getURL( self._target )

    def _setLang(self):
        lang=self._websession.getLang()
        Logger.get('i18n').debug("lang:%s"%lang)
        #if lang is None:
        #    lang = "en_US"
        from MaKaC import i18n
        i18n.install('messages', lang, unicode=True)


    accessWrapper = property( getAW )

class RH(RequestHandlerBase):
    """This class is the base for request handlers of the application. A request
        handler will be instantiated when a web request arrives to mod_python;
        the mp layer will forward the request to the corresponding request
        handler which will know which action has to be performed (displaying a
        web page or performing some operation and redirecting to another page).
        Request handlers will be responsible for parsing the parameters coming
        from a mod_python request, handle the errors which occurred during the
        action to perform, managing the sessions, checking security for each
        operation (thus they implement the access control system of the web
        interface).
        It is important to encapsulate all this here as in case of changing
        the web application framework we'll just need to adapt this layer (the
        rest of the system wouldn't need any change).

        Attributes:
            _uh - (URLHandler) Associated URLHandler which points to the
                current rh.
            _req - (mod_python.Request) mod_python request received for the
                current rh.
            _requestStarted - (bool) Flag which tells whether a DB transaction
                has been started or not.
            _websession - ( webinterface.session.sessionManagement.PSession )
                Web session associated to the HTTP request.
            _aw - (AccessWrapper) Current access information for the rh.
            _target - (Locable) Reference to an object which is the destination
                of the operations needed to carry out the rh. If set it must
                provide (through the standard Locable interface) the methods
                to get the url parameters in order to reproduce the access to
                the rh.
            _reqParams - (dict) Dictionary containing the received HTTP
                 parameters (independently of the method) transformed into
                 python data types. The key is the parameter name while the
                 value should be the received paramter value (or values).
    """
    _currentRH = None
    _tohttps = False

    def __init__( self, req ):
        """Constructor. Initialises the rh setting up basic attributes so it is
            able to process the request.

            Parameters:
                req - (mod_python.Request) mod_python request received for the
                    current rh.
        """
        if req == None:
            raise Exception("Request object not initialised")
        self._req = req
        self._requestStarted = False
        self._websession = None
        self._aw = AccessWrapper()  #Fill in the aw instance with the current information
        self._target = None
        self._reqParams = {}
        self._startTime = None
        self._endTime = None
        self._tempFilesToDelete = []
        self._doProcess = True  #Flag which indicates whether the RH process
                                #   must be carried out; this is useful for
                                #   the checkProtection methods when they
                                #   detect that an inmediate redirection is
                                #   needed
        RH._currentRH = self

    # Methods =============================================================

    def getHostIP(self):
        import socket

        host = str(self._req.get_remote_host(apache.REMOTE_NOLOOKUP))

        try:
            hostIP = socket.gethostbyname(host)
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            if minfo.useProxy():
                # if we're behind a proxy, use X-Forwarded-For
                xff = self._req.headers_in.get("X-Forwarded-For",hostIP).split(", ")[-1]
                return socket.gethostbyname(xff)
            else:
                return hostIP
        except socket.gaierror, e:
            # in case host resolution fails
            raise HostnameResolveError("Error resolving host '%s' : %s" % (host, e))


    def getTarget( self ):
        return self._target

    def _setSession( self ):
        """Sets up a reference to the corresponding web session. It uses the
            session manager to retrieve the session corresponding to the
            received request and makes sure it is a valid one. In case of having
            an invalid session it reset client settings and creates a new one.
       """
        if not self._websession:
            sm = session.getSessionManager()
            try:
                self._websession = sm.get_session( self._req )
            except session.SessionError, e:
                sm.revoke_session_cookie( self._req )
                self._websession = sm.get_session( self._req )
            sm.maintain_session( self._req, self._websession )

    def _getSession( self ):
        """Returns the web session associated to the received mod_python
            request.
        """
        if not self._websession:
            self._setSession()
        return self._websession

    def _setSessionUser( self ):
        """
        """
        self._aw.setUser( self._getSession().getUser() )

    def _getRequestParams( self ):
        return self._reqParams

    def getRequestParams( self ):
        return self._getRequestParams()

    def getRequestHTTPHeaders( self ):
        return self._req.headers_in

    def _disableCaching(self):
        """
        Disables caching, i.e. for materials
        """

        self._req.headers_out["Pragma"] = "no-cache"

        # IE doesn't seem to like 'no-cache' Cache-Control headers...
        if (re.match(r'.*MSIE.*', self._req.headers_in.get("User-Agent",""))):
            self._req.headers_out["Cache-Control"] = "private"
            self._req.headers_out["Expires"] = "-1"
        else:
            self._req.headers_out["Cache-Control"] = "no-store, no-cache, must-revalidate"


    def _redirect( self, targetURL, noCache=False ):
        """Utility for redirecting the client web browser to the specified
            URL.
            Params:
                newURL - Target URL of the redirection
        """
        #check if there is no \r\n character to avoid http header injection
        if str(targetURL):
            if "\r" in str(targetURL) or "\n" in str(targetURL):
                raise MaKaCError(_("http header CRLF injection detected"))
        self._req.headers_out["Location"] = str(targetURL)

        if noCache:
            self._disableCaching()
        try:
            self._req.status = apache.HTTP_MOVED_PERMANENTLY
        except NameError:
            pass

    def _checkHttpsRedirect(self):
        if self._tohttps and not self._req.is_https():
            current_url = self._req.construct_url(self._req.unparsed_uri)
            self._redirect(urlHandlers.setSSLPort(current_url.replace("http://", "https://")))
            return True
        else:
            return False

    def _normaliseListParam( self, param ):
        if not isinstance(param, list):
                return [ param ]
        return param

    def _processError( self, ex ):
        """
        """
        raise ex

    def _checkParams( self, params ):
        """
        """
        pass

    def _process( self ):
        """
        """
        pass

    def _processGeneralError(self,e):
        """Treats general errors occured during the process of a RH.
        """

        Logger.get('requestHandler').info('Request %s finished with: "%s"' % (id(self._req), e))

        p=errors.WPGenericError(self)
        return p.display()


    def _getTruncatedParams(self):
        """ Truncates params, so that file objects do not show up in the logs """

        params = {}

        for key,value in self._reqParams.iteritems():
            if isinstance(value, Field):
                params[key] = "<FILE>"
            elif type(value) == str:
                params[key] = truncate(value, 1024)
            else:
                params[key] = value

        return params

    def _processUnexpectedError(self,e):
        """Unexpected errors
        """

        Logger.get('requestHandler').exception('Request %s failed: "%s"\n\nurl: %s\n\nparameters: %s\n\n' % (id(self._req), e,self.getRequestURL(), self._getTruncatedParams()))
        p=errors.WPUnexpectedError(self)
        return p.display()

    def _processHostnameResolveError(self,e):
        """Unexpected errors
        """

        Logger.get('requestHandler').exception('Request %s failed: "%s"\n\nurl: %s\n\nparameters: %s\n\n' % (id(self._req), e,self.getRequestURL(), self._getTruncatedParams()))
        p=errors.WPHostnameResolveError(self)
        return p.display()


    def _processAccessError(self,e):
        """Treats access errors occured during the process of a RH.
        """
        Logger.get('requestHandler').info('Request %s finished with AccessError: "%s"' % (id(self._req), e))

        p=errors.WPAccessError(self)
        return p.display()

    def _processModificationError(self,e):
        """Treats modification errors occured during the process of a RH.
        """

        Logger.get('requestHandler').info('Request %s finished with ModificationError: "%s"' % (id(self._req), e))

        p=errors.WPModificationError(self)
        return p.display()

    def _processConferenceClosedError(self,e):
        """Treats access to modification pages for conferences when they are closed.
        """
        p = WPConferenceModificationClosed( self, e._conf )
        return p.display()

    def _processTimingError(self,e):
        """Treats timing errors occured during the process of a RH.
        """

        Logger.get('requestHandler').info('Request %s finished with TimingError: "%s"' % (id(self._req), e))

        p=errors.WPTimingError(self,e)
        return p.display()

    def _processNoReportError(self,e):
        """Process errors without reporting
        """

        Logger.get('requestHandler').info('Request %s finished with NoReportError: "%s"' % (id(self._req), e))

        p=errors.WPNoReportError(self,e)
        return p.display()

    def _processParentTimingError(self,e):
        """Treats timing errors occured during the process of a RH.
        """

        Logger.get('requestHandler').info('Request %s finished with ParentTimingError: "%s"' % (id(self._req), e))

        p=errors.WPParentTimingError(self,e)
        return p.display()

    def _processEntryTimingError(self,e):
        """Treats timing errors occured during the process of a RH.
        """

        Logger.get('requestHandler').info('Request %s finished with EntryTimingError: "%s"' % (id(self._req), e))

        p=errors.WPEntryTimingError(self,e)
        return p.display()

    def _processFormValuesError(self,e):
        """Treats timing errors occured during the process of a RH.
        """

        Logger.get('requestHandler').info('Request %s finished with FormValuesError: "%s"' % (id(self._req), e))

        p=errors.WPFormValuesError(self,e)
        return p.display()

    def _processHtmlScriptError(self, e):

        Logger.get('requestHandler').info('Request %s finished with ProcessHtmlScriptError: "%s"' % (id(self._req), e))

        p=errors.WPHtmlScriptError(self, escape(str(e)))
        return p.display()

    def _processRestrictedHTML(self, e):

        Logger.get('requestHandler').info('Request %s finished with ProcessRestrictedHTMLError: "%s"' % (id(self._req), e))

        p=errors.WPRestrictedHTML(self, escape(str(e)))
        return p.display()

    def process( self, params ):
        """
        """

        profile = Config.getInstance().getProfile()
        proffilename = ""
        res = ""
        retry = 10
        textLog = []
        self._startTime = datetime.now()

        # create the context
        ContextManager.create()

        #redirect to https if necessary
        if self._checkHttpsRedirect():
            return res

        DBMgr.getInstance().startRequest()
        self._startRequestSpecific2RH()     # I.e. implemented by Room Booking request handlers
        textLog.append("%s : Database request started"%(datetime.now() - self._startTime))
        Logger.get('requestHandler').info('[pid=%s] Request %s started (%s)' % (os.getpid(),id(self._req), self._req.unparsed_uri))
        try:
            while retry>0:
                try:
                    Logger.get('requestHandler').info('\t[pid=%s] from host %s' % (os.getpid(), self.getHostIP()))
                    try:
                        DBMgr.getInstance().sync()
                        # keep a link to the web session in the access wrapper
                        # this is used for checking access/modification key existence
                        # in the user session
                        self._aw.setIP( self.getHostIP() )
                        self._aw.setSession(self._getSession())
                        #raise(str(dir(self._websession)))
                        self._setSessionUser()
                        self._setLang()

                        if self._getUser():
                            Logger.get('requestHandler').debug('Request %s identified with user %s (%s)' % (id(self._req), self._getUser().getFullName(), self._getUser().getId()))

                        #if self._getUser() != None and self._getUser().getId() == "893":
                        #    profile = True
                        self._reqParams = copy.copy( params )
                        self._checkParams( self._reqParams )
                        self._checkProtection()
                        security.sanitizationCheck(self._target,
                                               self._reqParams,
                                               self._aw)
                        if self._doProcess:
                            if profile:
                                import profile, pstats
                                proffilename = os.path.join(Config.getInstance().getTempDir(), "stone%s.prof" % str(random.random()))
                                result = [None]
                                profile.runctx("result[0] = self._process()", globals(), locals(), proffilename)
                                res = result[0]
                            else:
                                res = self._process()
                        self._endRequestSpecific2RH( True ) # I.e. implemented by Room Booking request handlers

                        DBMgr.getInstance().endRequest( True )
                        Logger.get('requestHandler').info('Request %s successful' % (id(self._req)))

                        #request succesfull, now, doing tas that must be done only once
                        try:
                            self._sendEmails()
                            self._deleteTempFiles()
                        except:
                            pass
                        break
                    except MaKaCError, e:
                        #DBMgr.getInstance().endRequest(False)
                        res = self._processError(e)
                except ConflictError:
                    import traceback
                    Logger.get('requestHandler').debug('Conflict in Database! (Request %s)\n%s' % (id(self._req), traceback.format_exc()))
                    self._abortSpecific2RH()
                    DBMgr.getInstance().abort()
                    retry -= 1
                    continue
                except ClientDisconnected:
                    Logger.get('requestHandler').debug('Client Disconnected! (Request %s)' % id(self._req) )
                    self._abortSpecific2RH()
                    DBMgr.getInstance().abort()
                    retry -= 1
                    time.sleep(10-retry)
                    continue
        except AccessError, e:
            #Access error treatment
            res = self._processAccessError( e )
            self._endRequestSpecific2RH( False )
            DBMgr.getInstance().endRequest(False)
        except HostnameResolveError, e:
            res = self._processHostnameResolveError( e )
            self._endRequestSpecific2RH( False )
            DBMgr.getInstance().endRequest(False)
        except ModificationError, e:
            #Modification error treatment
            res = self._processModificationError( e )
            self._endRequestSpecific2RH( False )
            DBMgr.getInstance().endRequest(False)
        except ParentTimingError, e:
            #Modification error treatment
            res = self._processParentTimingError( e )
            self._endRequestSpecific2RH( False )
            DBMgr.getInstance().endRequest(False)
        except EntryTimingError, e:
            #Modification error treatment
            res = self._processEntryTimingError( e )
            self._endRequestSpecific2RH( False )
            DBMgr.getInstance().endRequest(False)
        except TimingError, e:
            #Modification error treatment
            res = self._processTimingError( e )
            self._endRequestSpecific2RH( False )
            DBMgr.getInstance().endRequest(False)
        except FormValuesError, e:
            #Error filling the values of a form
            res = self._processFormValuesError( e )
            self._endRequestSpecific2RH( False )
            DBMgr.getInstance().endRequest(False)
        except ConferenceClosedError, e:
            #Modification error treatment
            res = self._processConferenceClosedError( e )
            self._endRequestSpecific2RH( False )
            DBMgr.getInstance().endRequest(False)
        except NoReportError, e:
            #Error filling the values of a form
            res = self._processNoReportError( e )
            DBMgr.getInstance().endRequest(False)
        except htmlScriptError,e:
            res = self._processHtmlScriptError(e)
            DBMgr.getInstance().endRequest(False)
        except htmlForbiddenTag,e:
            res = self._processRestrictedHTML(e)
            DBMgr.getInstance().endRequest(False)
        except MaKaCError, e:
            res = self._processGeneralError( e )
            DBMgr.getInstance().endRequest(False)
        except ValueError, e:
            res = self._processGeneralError( e )
            DBMgr.getInstance().endRequest(False)
        except Exception, e: #Generic error treatment
            res = self._processUnexpectedError( e )
            #DBMgr.getInstance().endRequest(False)
            #self._endRequestSpecific2RH( False )

            #cancels any redirection
            try:
                del self._req.headers_out["Location"]
            except AttributeError:
                pass
            try:
                self._req.status=apache.HTTP_INTERNAL_SERVER_ERROR
            except NameError:
                pass



        #if we have an https request, we replace the links to Indico images by https ones.
        if self._req.is_https() and self._tohttps and res is not None:
            imagesBaseURL = Config.getInstance().getImagesBaseURL()
            imagesBaseSecureURL = urlHandlers.setSSLPort(Config.getInstance().getImagesBaseSecureURL())
            res = res.replace(imagesBaseURL, imagesBaseSecureURL)
            res = res.replace(escapeHTMLForJS(imagesBaseURL), escapeHTMLForJS(imagesBaseSecureURL))

        # destroy the context
        ContextManager.destroy()

        totalTime = (datetime.now() - self._startTime)
        textLog.append("%s : Request ended"%totalTime)

        # log request timing
        if profile and totalTime > timedelta(0, 1) and os.path.isfile(proffilename):
            rep = Config.getInstance().getTempDir()
            stats = pstats.Stats(proffilename)
            stats.strip_dirs()
            stats.sort_stats('cumulative', 'time', 'calls')
            stats.dump_stats(os.path.join(rep, "IndicoRequestProfile.log"))
            output = StringIO.StringIO()
            sys.stdout = output
            stats.print_stats(100)
            sys.stdout = sys.__stdout__
            s = output.getvalue()
            f = file(os.path.join(rep, "IndicoRequest.log"), 'a+')
            f.write("--------------------------------\n")
            f.write("URL     : " + self._req.construct_url(self._req.unparsed_uri) + "\n")
            f.write("%s : start request\n"%self._startTime)
            f.write("params:%s"%params)
            f.write("\n".join(textLog))
            f.write("\n")
            f.write("retried : %d\n"%(10-retry))
            f.write(s)
            f.write("--------------------------------\n\n")
            f.close()
        if profile and proffilename != "" and os.path.exists(proffilename):
            os.remove(proffilename)

        if res == "" or res == None:
            return "[done]"

        return res

    def _sendEmails( self ):
        if hasattr( self, "_emailsToBeSent" ):
            for email in self._emailsToBeSent:
                GenericMailer.send(GenericNotification(email))

    def _deleteTempFiles( self ):
        if len(self._tempFilesToDelete) > 0:
            for file in self._tempFilesToDelete:
                os.remove(file)

    def getRequestURL( self ):
        proc = "http://"
        try:
            if self._req.is_https():
                proc = "https://"
        except:
            pass

        port = ""
        if self._req.parsed_uri[apache.URI_PORT]:
            port = ":" + str( self._req.parsed_uri[apache.URI_PORT] )
        return "%s%s%s%s"%(proc, self._req.hostname, port, self._req.unparsed_uri)

    def _startRequestSpecific2RH( self ):
        """
        Works like DBMgr.getInstance().startRequest() but is specific to
        request handler. It is used to connect to other database only
        in choosen request handlers.

        I.e. all Room Booking request handlers override this
        method to connect to Room Booking backend.
        """
        pass

    def _endRequestSpecific2RH( self, commit ):
        """
        Works like DBMgr.getInstance().endRequest() but is specific to
        request handler. It is used to disconnect from other database only
        in choosen request handlers.

        I.e. all Room Booking request handlers override this
        method to disconnect from Room Booking backend.
        """
        pass

    def _syncSpecific2RH( self ):
        """
        Works like DBMgr.getInstance().sync() but is specific to
        request handler. It is used to connect to other database only
        in choosen request handlers.

        I.e. all Room Booking request handlers override this
        method to sync backend.
        """
        pass

    def _abortSpecific2RH( self ):
        """
        Works like DBMgr.getInstance().abort() but is specific to
        request handler. It is used to abort transactions of other database
        only in choosen request handlers.

        I.e. all Room Booking request handlers override this method.
        """
        pass

    # Properties =============================================================

    requestURL = property( getRequestURL )
    relativeURL = None


from MaKaC.rb_location import CrossLocationDB
import MaKaC.common.info as info

class RoomBookingDBMixin:     # It's _not_ RH
    """
    Goal:
    Only _some_ Request Handlers should connect to
    room booking database.

    Mix in this class into all Request Handlers,
    which must use Room Booking backend.

    Usage:

    class RHExample( RoomBookingDBMixin, RHProtected ):
        pass

    NOTE: it is important to put RoomBookingDBMixin as first
    base class.
    """

    def _startRequestSpecific2RH( self ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getRoomBookingModuleActive():
            CrossLocationDB.connect()

    def _endRequestSpecific2RH( self, commit = True ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getRoomBookingModuleActive():
            if commit: CrossLocationDB.commit()
            else: CrossLocationDB.rollback()
            CrossLocationDB.disconnect()

    def _syncSpecific2RH( self ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getRoomBookingModuleActive():
            CrossLocationDB.sync()

    def _abortSpecific2RH( self ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getRoomBookingModuleActive():
            CrossLocationDB.rollback()


class RHProtected( RH ):

    def _getLoginURL( self ):
        #url = self.getCurrentURL()
        url = self.getRequestURL()
        if url == "":
            url = urlHandlers.UHWelcome.getURL()
        return urlHandlers.UHSignIn.getURL( url )

    def _checkSessionUser( self ):
        """
        """

        if self._getUser() == None:
            self._redirect( self._getLoginURL() )
            self._doProcess = False

    def _checkProtection( self ):
        self._checkSessionUser()


class RHDisplayBaseProtected( RHProtected ):

    def _checkProtection( self ):

        if not self._target.canAccess( self.getAW() ):
            from MaKaC.conference import Link, LocalFile, Category
            if isinstance(self._target,Link) or isinstance(self._target,LocalFile):
                target = self._target.getOwner()
            else:
                target = self._target
            if not isinstance(self._target, Category):
                if target.getAccessKey() != "" or target.getConference().getAccessKey() != "":
                    raise AccessError()
            if self._getUser() == None:
                self._checkSessionUser()
            else:
                raise AccessError()


class RHModificationBaseProtected( RHProtected ):

    def _checkProtection( self ):
        if not self._target.canModify( self.getAW() ):
            if self._target.getModifKey() != "":
                raise ModificationError()
            if self._getUser() == None:
                self._checkSessionUser()
            else:
                raise ModificationError()
        if hasattr(self._target, "getConference"):
            if self._target.getConference().isClosed():
                raise ConferenceClosedError(self._target.getConference())

