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

"""Some pages for dealing with generic application errors
"""
from flask import session, request
import traceback
import sys
from xml.sax.saxutils import quoteattr

import MaKaC.webinterface.urlHandlers as urlHandlers
from indico.core.config import Config
from MaKaC.webinterface.pages.base import WPDecorated
from MaKaC.webinterface.wcomponents import WTemplated
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.i18n import _
from indico.util.i18n import i18nformat

class WGenericError( WTemplated ):

    def __init__( self, rh, showDetails=False ):
        self._rh = rh
        self._showDetails = showDetails


    def getVars( self ):
        vars = WTemplated.getVars( self )
        ex = sys.exc_info()[1]
        vars["msg"] = self.htmlText( str( ex ) )
        vars["area"]= ""
        ty, ex, tb = sys.exc_info()
        tracebackList = traceback.format_list( traceback.extract_tb( tb ) )
        rh = self._rh.__class__
        url = request.url.encode('utf-8')
        params = []
        for (k,v) in self._rh.getRequestParams().items():
            if k.strip() != "password":
                params.append("""%s = %s""" % (self.htmlText(k), self.htmlText(v)))
        headers = []
        for k, v in request.headers.iteritems():
            headers.append("""%s: %s""" % (self.htmlText(k), self.htmlText(v)))
        userHTML = """-- none --"""
        vars["userEmail"] = ""
        av = self._rh.getAW().getUser()
        if av:
            userHTML = self.htmlText( "%s <%s>"%( av.getFullName(), av.getEmail() ) )
            vars["userEmail"] = quoteattr( av.getEmail() )
        vars["reportURL"] = quoteattr( str( urlHandlers.UHErrorReporting.getURL() ) )
        details = ""
        if HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive():
            details = """
<table class="errorDetailsBox">
    <tr>
        <td>ERROR DETAILS</td>
    </tr>
    <tr>
        <td><br></td>
    </tr>
    <tr>
        <td nowrap align="right"><b>Exception type:</b></td>
        <td>%s</td>
    </tr>
    <tr>
        <td nowrap align="right" valign="top"><b>Exception message:</b></td>
        <td>%s</td>
    </tr>
    """%( self.htmlText( str(ty) ), self.htmlText( str(ex) ))

            if hasattr(ex, 'problematic_templates') and hasattr(ex, 'template_tracebacks'):
                for i in range(len(ex.problematic_templates)):
                    details +="""
    <tr>
        <td nowrap align="right" valign="top"><b>Traceback for<br>%s.tpl:</b></td>
        <td>%s</td>
    </tr>
                """%(ex.problematic_templates[i], "<br>".join(ex.template_tracebacks[i]))

            details +="""
    <tr>
        <td valign="top" nowrap align="right"><b>Traceback:</b></td>
        <td><pre>%s</pre></td>
    </tr>
    <tr>
        <td nowrap align="right"><b>Request handler:</b></td>
        <td>%s</td>
    </tr>
    <tr>
        <td nowrap align="right"><b>URL:</b></td>
        <td>%s</td>
    </tr>
    <tr>
        <td nowrap align="right" valign="top"><b>Params:</b></td>
        <td>%s</td>
    </tr>
    <tr>
        <td valign="top" nowrap align="right"><b>HTTP headers:</b></td>
        <td><pre>%s</pre></td>
    </tr>
    <tr>
        <td nowrap align="right"><b>Logged user:</b></td>
        <td>%s</td>
    </tr>
</table>
            """%("\n".join( tracebackList ), rh.__name__, url, "<br>".join(params), \
                    "\n".join( headers ), userHTML )
        vars["errorDetails"] = details
        userStr = """-- "none" --"""
        if av:
            userStr = "[%s] %s <%s>"%(av.getId(), av.getFullName(), av.getEmail() )
        report = ["exception message => %s"%str( ex ), \
                    "exception type => %s" %str(ty), \
                    "traceback => \n%s"%"\n".join(tracebackList), \
                    "request handler => %s"%self._rh.__class__, \
                    "url => %s" % request.url.encode('utf-8'),
                    "parameters => \n%s"%"\n".join(params), \
                    "headers => \n%s"%"\n".join(headers), \
                    "user => %s"%userStr ]
        vars["reportMsg"] = quoteattr( "\n".join( report ) )
        return vars

class WUnexpectedError( WGenericError ):
    pass


class WPGenericError( WPDecorated ):

    def __init__( self, rh):
        WPDecorated.__init__( self, rh )


    def _getBody( self, params ):
        wc = WGenericError( self._rh, params.get("showDetails", False) )
        return wc.getHTML()

class WPUnexpectedError( WPDecorated ):

    def __init__( self, rh):
        WPDecorated. __init__( self, rh )


    def _getBody( self, params ):
        wc = WUnexpectedError( self._rh )
        return wc.getHTML()

class WAccessError( WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["area"]= i18nformat(""" _("Authorisation") - """)
        vars["msg"] = _("The access to this page has been restricted by its owner and you are not authorised to view it")
        if isinstance(self._rh._target, list):
            #only objects with Access Controler (e.g. we do not want to check this for RB reservertion target): Conferences, Contribs...
            contactInfo = [item.getAccessController().getAnyContactInfo() for item in self._rh._target if hasattr(item, 'getAccessController') ]
            vars["contactInfo"] = ";".join(contactInfo)
        elif self._rh._target is not None and hasattr(self._rh._target, 'getAccessController'): #only objects with Access Controler (e.g. we do not want to check this for RB reservertion target): Conferences, Contribs...
            vars["contactInfo"] = self._rh._target.getAccessController().getAnyContactInfo()
        else:
            vars["contactInfo"] = ""
        return vars

class WAccessKeyError( WTemplated ):

    def __init__( self, rh, msg="" ):
        self._rh = rh
        self._msg = msg

    def getVars( self ):
        from MaKaC.conference import Conference,Material, Resource
        vars = WTemplated.getVars( self )
        vars["loginURL"] = ""
        if self._rh._getUser() is None:
            vars["loginURL"] = str(urlHandlers.UHSignIn.getURL(returnURL=request.url))
        if isinstance(self._rh._target,Conference):
            vars["type"] = "event"
            vars["url"] = quoteattr( str( urlHandlers.UHConfEnterAccessKey.getURL(self._rh._target) ) )
        elif isinstance(self._rh._target,Material):
            vars["type"] = "file"
            vars["url"] = quoteattr( str( urlHandlers.UHMaterialEnterAccessKey.getURL(self._rh._target) ) )
        elif isinstance(self._rh._target,Resource):
            vars["type"] = "file"
            vars["url"] = quoteattr( str( urlHandlers.UHFileEnterAccessKey.getURL(self._rh._target) ) )
        else:
            vars["type"] = "presentation"
            vars["url"] = quoteattr( str( urlHandlers.UHConfEnterAccessKey.getURL(self._rh._target.getConference()) ) )
        vars["msg"] = self._msg
        return vars


class WPAccessError( WPDecorated ):

    def __init__( self, rh ):
        WPDecorated.__init__( self, rh )

    def _getBody( self, params ):
        wc = WAccessError( self._rh )
        return wc.getHTML()


class WPKeyAccessError( WPDecorated ):

    def __init__( self, rh ):
        WPDecorated.__init__( self, rh )

    def _getBody( self, params ):
        tgt = self._rh._target
        msg = ""
        keys = session.get("accessKeys", {})
        if tgt.getUniqueId() in keys:
            msg = i18nformat("""<font color=red> _("Bad access key")!</font>""")
        else:
            msg = ""
        wc = WAccessKeyError( self._rh, msg )
        return wc.getHTML()


class WPLaTeXError(WPDecorated):

    def __init__(self, rh, error):
        WPDecorated.__init__(self, rh)
        self._error = error

    def _getBody( self, params ):
        wc = WTemplated('LaTeXError')
        conf = self._error.params['conf']
        return wc.getHTML({
            'report_id': self._error.report_id,
            'is_manager': conf.canModify(self._getAW()),
            'log': open(self._error.log_file, 'r').read(),
            'source_code': open(self._error.source_file, 'r').read()
            })


class WTimingError( WTemplated ):

    def __init__( self, rh, msg="" ):
        self._rh = rh
        self._msg = msg

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["msg"] = self._msg
        vars["urlbase"] = Config.getInstance().getBaseURL()
        return vars

class WParentTimingError( WTimingError ):
    pass

class WEntryTimingError( WTimingError ):
    pass

class WPTimingError( WPDecorated ):

    def __init__( self, rh, msg="" ):
        self._msg = msg
        WPDecorated. __init__( self, rh)

    def _getBody( self, params ):
        wc = WTimingError( self._rh, self._msg )
        return wc.getHTML()

class WPParentTimingError( WPTimingError ):

    def _getBody( self, params ):
        wc = WParentTimingError( self._rh, self._msg )
        return wc.getHTML()

class WPEntryTimingError( WPTimingError ):

    def _getBody( self, params ):
        wc = WEntryTimingError( self._rh, self._msg )
        return wc.getHTML()

class WModificationError( WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )
        return vars


class WModificationKeyError( WTemplated ):

    def __init__( self, rh, msg="" ):
        self._rh = rh
        self._msg = msg

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["loginURL"] = ""
        if self._rh._getUser() is None:
            vars["loginURL"] = str(urlHandlers.UHSignIn.getURL(returnURL=request.url))
        vars["msg"] = self._msg
        redirectURL = ""
        if hasattr(self._rh, "_redirectURL"):
            redirectURL = self._rh._redirectURL
        vars["redirectURL"] = quoteattr(redirectURL)
        vars["url"] = quoteattr( str( urlHandlers.UHConfEnterModifKey.getURL(self._rh._target) ) )
        return vars


class WPModificationError( WPDecorated ):

    def __init__( self, rh ):
        WPDecorated.__init__( self, rh )

    def _getBody( self, params ):
        if hasattr(self._rh._target, "getModifKey") and \
            self._rh._target.getModifKey() != "":
            keys = session.get("modifKeys", {})
            if keys.get(self._rh._target.getId()):
                msg = i18nformat("""<font color=red> _("Wrong modification key!")</font>""")
            else:
                msg = ""
            wc = WModificationKeyError( self._rh, msg )
        else:
            wc = WModificationError( self._rh )
        return wc.getHTML()


class WReportError( WTemplated ):

    def __init__( self, dstMail, msg ):
        WTemplated.__init__(self)
        self._dstMail = dstMail
        self._msg = msg

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["postURL"] = quoteattr( str( urlHandlers.UHErrorReporting.getURL() ) )
        vars["dstEmail"] = quoteattr( self._dstMail )
        vars["reportMsg"] = quoteattr( self._msg )
        return vars


class WPReportError( WPDecorated ):

    def __init__( self, rh):
        WPDecorated.__init__(self, rh)#, True)

    def _getHTMLHeader(self):
        return ""

    def _getHeader(self):
        return ""

    def _getBody( self, params ):
        wc = WReportError( params["userEmail"], params["msg"] )
        return wc.getHTML( params )

    def _getFooter( self ):
        return ""

class WNoReportError( WTemplated ):

    def __init__( self, msg ):
        self._msg = msg

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["msg"] = self._msg
        return vars


class WPNoReportError( WPDecorated ):

    def __init__( self, rh, msg ):
        self._msg = msg
        WPDecorated. __init__( self, rh)

    def _getHeader(self):
        return ""

    def _getBody( self, params ):
        wc = WNoReportError( self._msg )
        return wc.getHTML( params )

class WReportErrorSummary( WTemplated ):
    pass


class WPReportErrorSummary( WPDecorated ):

    def __init__( self, rh ):
        WPDecorated. __init__( self, rh)

    def _getHTMLHeader( self ):
        return ""

    def _getHeader( self ):
        return ""

    def _getBody( self, params ):
        wc = WReportErrorSummary()
        return wc.getHTML()

    def _getFooter( self ):
        return ""

class WFormValuesError( WTemplated ):

    def __init__( self, rh, msg="" ):
        self._rh = rh
        self._msg = msg

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["msg"] = self._msg
        return vars

class WPFormValuesError( WPDecorated ):

    def __init__( self, rh, msg="" ):
        self._msg = msg
        WPDecorated. __init__( self, rh)

    def _getBody( self, params ):
        wc = WFormValuesError( self._rh, self._msg )
        return wc.getHTML()


class WPRestrictedHTML( WPDecorated ):

    def __init__( self, rh, msg="" ):
        self._msg = msg
        WPDecorated. __init__( self, rh)

    def _getBody( self, params ):
        wc = WRestrictedHTML( self._rh, self._msg )
        return wc.getHTML()

class WRestrictedHTML( WGenericError ):

    def __init__( self, rh, msg="" ):
        self._rh = rh
        self._msg = msg

    def getVars( self ):
        vars = WGenericError.getVars( self )
        vars["msg"] = self._msg
        return vars

class WPError404( WPMainBase ):

    def __init__( self, rh, goBack="" ):
        WPMainBase. __init__( self, rh)
        self._goBack = goBack

    def _getBody( self, params ):
        wc = WError404( self._rh, self._goBack )
        return wc.getHTML()

class WError404( WTemplated ):

    def __init__( self, rh, goBack="" ):
        self._rh = rh
        self._goBack = goBack

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["goBack"] = self._goBack
        return vars

