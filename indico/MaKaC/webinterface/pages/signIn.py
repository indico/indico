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

import MaKaC.webinterface.pages.base as base
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents


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


class WPResetPasswordBase:
    def _getBody(self, params):
        return wcomponents.WResetPassword().getHTML()


class WPResetPassword(WPResetPasswordBase, base.WPDecorated):
    pass


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
