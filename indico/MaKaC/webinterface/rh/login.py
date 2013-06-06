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
from flask import session

import os
from MaKaC.common import Configuration, Config
import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.rh.conferenceBase as conferenceBase
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.mail as mail
import MaKaC.webinterface.pages.signIn as signIn
from MaKaC.user import LoginInfo
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.user import AvatarHolder
from MaKaC.common import pendingQueues
import MaKaC.common.timezoneUtils as timezoneUtils
from MaKaC.errors import UserError
import MaKaC.common.info as info
from indico.web.flask.util import send_file

class RHSignIn( base.RH ):

    _tohttps = True
    _isMobile = False

    def _checkParams( self, params ):
        self._signIn = params.get("signIn", "").strip()
        self._login = params.get( "login", "" ).strip()
        self._password = params.get( "password", "" )
        self._returnURL = params.get( "returnURL", "").strip()
        if self._returnURL == "":
            self._returnURL = urlHandlers.UHWelcome.getURL()
        self._userId = params.get( "userId", "").strip()

    def _process( self ):
        self._disableCaching()
        #Check for automatic login
        auth = AuthenticatorMgr()
        av = auth.autoLogin(self)
        if av:
            url = self._returnURL
            tzUtil = timezoneUtils.SessionTZ(av)
            tz = tzUtil.getSessionTZ()
            session.timezone = tz
            session.user = av
            if Config.getInstance().getBaseSecureURL().startswith('https://'):
                url = str(url).replace('http://', 'https://')
            self._redirect(url)
        if not self._signIn:
            p = signIn.WPSignIn( self )
            return p.display( returnURL = self._returnURL )
        else:
            li = LoginInfo( self._login, self._password )
            av = auth.getAvatar(li)
            if not av:
                p = signIn.WPSignIn( self, login = self._login, msg = _("Wrong login or password") )
                return p.display( returnURL = self._returnURL )
            elif not av.isActivated():
                if av.isDisabled():
                    self._redirect(urlHandlers.UHDisabledAccount.getURL(av))
                else:
                    self._redirect(urlHandlers.UHUnactivatedAccount.getURL(av))
                return _("your account is not activate\nPlease active it and retry")
            else:
                url = self._returnURL
                session.user = av
                tzUtil = timezoneUtils.SessionTZ(av)
                tz = tzUtil.getSessionTZ()
                session.timezone = tz

            if self._userId != "":
                if "?" in url:
                    url += "&userId=%s"%self._userId
                else:
                    url += "?userId=%s"%self._userId
            if Config.getInstance().getBaseSecureURL().startswith('https://'):
                url = str(url).replace('http://', 'https://')
            self._redirect(url)


class RHSignOut( base.RH ):

    _isMobile = False

    def _checkParams( self, params ):
        self._returnURL = params.get( "returnURL", "").strip()
        if self._returnURL == "":
            self._returnURL = urlHandlers.UHWelcome.getURL()

    def _process( self ):
        autoLogoutRedirect = None
        if self._getUser():
            auth = AuthenticatorMgr()
            autoLogoutRedirect = auth.autoLogout(self)
            session.clear()
            self._setUser(None)
        if autoLogoutRedirect:
            self._redirect(autoLogoutRedirect)
        else:
            self._redirect(self._returnURL)


class RHLogoutSSOHook( base.RH):

    _isMobile = False

    def _process(self):
        """Script triggered by the display of the centralized SSO logout
        dialog. It logouts the user from CDS Invenio and stream back the
        expected picture."""
        if self._getUser():
            auth = AuthenticatorMgr()
            auth.autoLogout(self)
            session.clear()
            self._setUser(None)
        path = os.path.join(Configuration.Config.getInstance().getImagesDir(), 'wsignout.gif')
        return send_file('wsignout.gif', path, 'GIF', inline=True)


class RHActive( base.RH ):

    _isMobile = False

    def _checkParams( self, params ):
        base.RH._checkParams(self, params )
        self._userId = params.get( "userId", "" ).strip()
        self._key = params.get( "key", "" ).strip()


    def _process( self ):

        av = AvatarHolder().getById(self._userId)
        if av.isActivated():
            p = signIn.WPAccountAlreadyActivated( self, av )
            return p.display()
            #return "your account is already activated"
        if av.isDisabled():
            p = signIn.WPAccountDisabled( self, av )
            return p.display()
            #return "your account is disabled. please, ask to enable it"
        elif self._key == av.getKey():
            av.activateAccount()
            p = signIn.WPAccountActivated( self, av )
            return p.display()
            #return "Your account is activate now"
        else:
            return "Wrong key. Please, ask for a new one"
            pass


class RHSendLogin( base.RH ):

    _isMobile = False

    def _checkParams( self, params ):
        self._userId = params.get( "userId", "" ).strip()
        self._email = params.get("email", "").strip()

    def _process( self ):
        av = None
        if self._userId:
            av = AvatarHolder().getById(self._userId)
        elif self._email:
            try:
                av = AvatarHolder().match({"email":self._email}, exact=1)[0]
            except:
                pass
        if av:
            sm = mail.sendLoginInfo(av)
            sm.send()
        self._redirect(urlHandlers.UHSignIn.getURL() )


class RHSendActivation( base.RH ):

    _isMobile = False

    def _checkProtection( self ):
        base.RH._checkProtection(self)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getModerateAccountCreation():
            raise UserError("Impossible to send activation email because the account creation is moderated")


    def _checkParams( self, params ):
        base.RH._checkParams(self, params )
        self._userId = params.get( "userId", "" ).strip()

    def _process( self ):
        av = AvatarHolder().getById(self._userId)
        sm = mail.sendConfirmationRequest(av)
        sm.send()
        self._redirect(urlHandlers.UHSignIn.getURL())


class RHDisabledAccount( base.RH ):

    _isMobile = False

    def _checkParams( self, params ):
        base.RH._checkParams(self, params )
        self._userId = params.get( "userId", "" ).strip()

    def _process( self ):
        av = AvatarHolder().getById(self._userId)
        p = signIn.WPAccountDisabled( self, av )
        return p.display()

class RHUnactivatedAccount( base.RH ):

    _isMobile = False

    def _checkParams( self, params ):
        base.RH._checkParams(self, params )
        self._userId = params.get( "userId", "" ).strip()

    def _process( self ):
        av = AvatarHolder().getById(self._userId)
        p = signIn.WPUnactivatedAccount( self, av )
        return p.display()
