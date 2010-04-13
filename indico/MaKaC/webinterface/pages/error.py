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

import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.pages.base import WPDecorated
from MaKaC.webinterface.wcomponents import WTemplated
from MaKaC.i18n import _

class WPError(WPDecorated):
    
    def __init__(self, rh, ex, params):
        WPDecorated.__init__(self, rh)
        self._ex = ex
        self._RHParams = params
        
    
    def _getBody(self, params):
        wc = WError(self._ex)
        msg = []
        msg.append("%s: %s"%( "error message", self._ex))
        msg.append("%s: %s"%( "url", self._rh._req.unparsed_uri))
        msg.append("%s: %s"%( "redirect from", self._rh._req.prev))
        msg.append("%s: %s"%( "headers", self._rh._req.headers_in ))
        for k in self._RHParams.keys():
            if k.strip() in ["password", "passwordBis"]:
                msg.append("%s: %s"%(k, self._RHParams[k]))
            else:
                #print * instead of password
                msg.append("%s: %s"%(k, "*"*len(self._RHParams[k])))
        
        msg.append("%s: %s"%("RequestHandlers", self._rh.__class__))
        
        params["msg"] = "\n".join(msg)
        params["email"] = ""
        if self._getAW().getUser():
            params["email"] = self._getAW().getUser().getEmail()
        return wc.getHTML(params)


class WError(WTemplated):
    
    def __init__(self, ex):
        self._ex = ex
    
    
    def getVars(self):
        vars = WTemplated.getVars(self)
        vars["errorText"] = "%s"%self._ex
        vars["sendReportURL"] = urlHandlers.UHErrorSendReport.getURL()
        return vars


class WPReportSended(WPDecorated):
    
    
    def __init__( self, rh):
        WPDecorated.__init__(self, rh)
    
    def _getBody(self, params):
        wc = WReportSended()
        return wc.getHTML(params)


class WReportSended(WTemplated):
       
    def getVars(self):
        vars = WTemplated.getVars(self)
        
        return vars

