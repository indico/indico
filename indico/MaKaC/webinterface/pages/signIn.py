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

import MaKaC.webinterface.pages.base as base
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.common.general import *


class WPSignIn( base.WPDecorated ):
    
    def __init__(self, rh, login="", msg = ""):
        self._login = login
        self._msg = msg
        base.WPDecorated.__init__( self, rh)
    
    def _getBody( self, params ):
        wc = wcomponents.WSignIn()
        p = {"postURL": urlHandlers.UHSignIn.getURL(), \
                "returnURL": params["returnURL"], \
                "createAccountURL": urlHandlers.UHUserCreation.getURL(), \
                "forgotPassordURL": urlHandlers.UHSendLogin.getURL(), \
                "login": self._login, \
                "msg": self._msg }
        return wc.getHTML( p )


class WPAccountAlreadyActivated( base.WPDecorated ):
    
    def __init__(self, rh, av):
        base.WPDecorated.__init__( self, rh)
        self._av = av
    
    def _getBody( self, params ):
        wc = wcomponents.WAccountAlreadyActivated( self._av)
        params["mailLoginURL"] = urlHandlers.UHSendLogin.getURL(self._av)
        
        return wc.getHTML( params )


class WPAccountActivated( base.WPDecorated ):
    
    def __init__(self, rh, av):
        base.WPDecorated.__init__( self, rh)
        self._av = av
    
    def _getBody( self, params ):
        wc = wcomponents.WAccountActivated( self._av)
        params["mailLoginURL"] = urlHandlers.UHSendLogin.getURL(self._av)
        params["loginURL"] = urlHandlers.UHSignIn.getURL()
        
        return wc.getHTML( params )


class WPAccountDisabled( base.WPDecorated ):
    
    def __init__(self, rh, av):
        base.WPDecorated.__init__( self, rh)
        self._av = av
    
    def _getBody( self, params ):
        wc = wcomponents.WAccountDisabled( self._av)
        #params["mailLoginURL"] = urlHandlers.UHSendLogin.getURL(self._av)
        
        return wc.getHTML( params )


class WPUnactivatedAccount( base.WPDecorated ):
    
    def __init__(self, rh, av):
        base.WPDecorated.__init__( self, rh)
        self._av = av
    
    def _getBody( self, params ):
        wc = wcomponents.WUnactivatedAccount( self._av)
        params["mailActivationURL"] = urlHandlers.UHSendActivation.getURL(self._av)
        
        return wc.getHTML( params )
