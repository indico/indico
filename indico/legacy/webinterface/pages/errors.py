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

import json
import sys
import traceback
from xml.sax.saxutils import quoteattr

from flask import session, request

from indico.core.config import Config
from indico.legacy.webinterface.pages.base import WPDecorated
from indico.legacy.webinterface.pages.main import WPMainBase
from indico.legacy.webinterface.wcomponents import WTemplated
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.util import get_request_info


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
        vars["reportURL"] = quoteattr(url_for('misc.errors'))
        details = ""
        show_details = Config.getInstance().getDebug()
        if not show_details:
            try:
                show_details = session.user and session.user.is_admin
            except Exception:
                # We are handling some error so we cannot know if accessing the session user works
                # If it fails we simply don't show details...
                pass
        if show_details:
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
        vars["reportMsg"] = quoteattr(json.dumps({'request_info': get_request_info(),
                                                  'traceback': traceback.format_exc()}))
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
        from indico.modules.events.legacy import LegacyConference
        vars = WTemplated.getVars( self )
        vars["area"]= _("Authorisation")
        vars["msg"] = _("The access to this page has been restricted by its owner and you are not authorised to view it")
        vars["contactInfo"] = ""
        if isinstance(self._rh._target, LegacyConference):
            vars["contactInfo"] = self._rh._target.as_event.no_access_contact
        return vars

class WAccessKeyError( WTemplated ):

    def __init__( self, rh, msg="" ):
        self._rh = rh
        self._msg = msg

    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars["url"] = url_for('event.conferenceDisplay-accessKey', self._rh._target)
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

    def _getBody(self, params):
        event = self._rh.event_new
        msg = ""
        has_key = session.get("access_keys", {}).get(event._access_key_session_key) is not None
        if has_key:
            msg = '<font color=red>{}</font>'.format(_("Bad access key!"))
        wc = WAccessKeyError( self._rh, msg )
        return wc.getHTML()


class WModificationError( WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )
        return vars


class WPModificationError( WPDecorated ):

    def __init__( self, rh ):
        WPDecorated.__init__( self, rh )

    def _getBody( self, params ):
        return WModificationError(self._rh).getHTML()


class WReportError( WTemplated ):

    def __init__( self, dstMail, msg ):
        WTemplated.__init__(self)
        self._dstMail = dstMail
        self._msg = msg

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["postURL"] = quoteattr(url_for('misc.errors'))
        vars["dstEmail"] = quoteattr( self._dstMail )
        vars["reportMsg"] = quoteattr( self._msg )
        return vars


class WPReportError(WPDecorated):
    def __init__(self, rh):
        WPDecorated.__init__(self, rh)

    def _getBody(self, params):
        wc = WReportError(params["userEmail"], params["msg"])
        return wc.getHTML(params)

    def _applyDecoration(self, body):
        return body

    def display(self, **params):
        return WPDecorated._display(self, params)


class WNoReportError( WTemplated ):

    def __init__( self, msg ):
        self._msg = msg

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["msg"] = self._msg
        return vars


class WPNoReportError(WPDecorated):
    def __init__(self, rh, msg):
        self._msg = msg
        WPDecorated.__init__(self, rh)

    def _getBody(self, params):
        return WNoReportError(self._msg).getHTML(params)


class WReportErrorSummary( WTemplated ):
    pass


class WPReportErrorSummary(WPDecorated):
    def __init__(self, rh):
        WPDecorated.__init__(self, rh)

    def _getBody(self, params):
        return WReportErrorSummary().getHTML()

    def _applyDecoration(self, body):
        return body

    def display(self, **params):
        return WPDecorated._display(self, params)


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
