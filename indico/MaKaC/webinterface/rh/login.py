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
from flask import session, request

import os
from indico.core.config import Config
from MaKaC.common.cache import GenericCache
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
from MaKaC.errors import UserError, MaKaCError, FormValuesError, NoReportError
import MaKaC.common.info as info
from indico.web.flask.util import send_file


class RHSignInBase(base.RH):

    _tohttps = True
    _isMobile = False

    def _checkParams(self, params):
        self._login = params.get("login", "").strip()
        self._password = params.get("password", "")
        self._doNotSanitizeFields.append("password")
        self._returnURL = params.get("returnURL", "").strip()
        if self._returnURL:
            session['loginReturnURL'] = self._returnURL

    def _setSessionVars(self, av):
        if not self._returnURL:
            self._returnURL = session.pop('loginReturnURL', urlHandlers.UHWelcome.getURL())
        self._url = self._returnURL
        tzUtil = timezoneUtils.SessionTZ(av)
        tz = tzUtil.getSessionTZ()
        session.timezone = tz
        session.user = av
        if Config.getInstance().getBaseSecureURL().startswith('https://'):
            self._url = str(self._url).replace('http://', 'https://')

    def _makeLoginProcess( self ):
        #Check for automatic login
        authManager = AuthenticatorMgr()
        if (authManager.isSSOLoginActive() and len(authManager.getList()) == 1 and
           not Config.getInstance().getDisplayLoginPage()):
            self._redirect(urlHandlers.UHSignInSSO.getURL(authId=authManager.getDefaultAuthenticator().getId()))
            return
        if request.method != 'POST':
            return self._signInPage.display(returnURL=self._returnURL)
        else:
            li = LoginInfo( self._login, self._password )
            av = authManager.getAvatar(li)
            if not av:
                return self._signInPageFailed.display( returnURL = self._returnURL )
            elif not av.isActivated():
                if av.isDisabled():
                    self._redirect(self._disabledAccountURL(av))
                else:
                    self._redirect(self._unactivatedAccountURL(av))
                return _("your account is not activate\nPlease active it and retry")
            else:
                self._setSessionVars(av)
            self._addExtraParamsToURL()
            self._redirect(self._url)


class RHSignIn( RHSignInBase ):

    def _checkParams( self, params ):
        RHSignInBase._checkParams(self, params)
        if self._returnURL == "":
            self._returnURL = urlHandlers.UHWelcome.getURL()
        self._userId = params.get( "userId", "").strip()
        self._disableCaching()
        self._disabledAccountURL = lambda av: urlHandlers.UHDisabledAccount.getURL(av)
        self._unactivatedAccountURL = lambda av: urlHandlers.UHUnactivatedAccount.getURL(av)
        self._signInPage = signIn.WPSignIn( self )
        self._signInPageFailed = signIn.WPSignIn( self, login = self._login, msg = _("Wrong login or password") )

    def _addExtraParamsToURL(self):
        if self._userId != "":
            if "?" in self._url:
                self._url += "&userId=%s"%self._userId
            else:
                self._url += "?userId=%s"%self._userId

    def _process(self):
        return self._makeLoginProcess()


class RHSignInSSO(RHSignInBase):

    _isMobile = False

    def _checkParams(self, params):
        self._authId = params.get('authId', '').strip()
        self._returnURL = params.get('returnURL', '')

    def _process(self):
        authenticator = session.pop('Authenticator', None)
        if authenticator is not None:
            authManager = AuthenticatorMgr()
            if not authManager.isSSOLoginActive():
                raise MaKaCError(_("SSO Login is not active."))
            av = authManager.SSOLogin(self, authenticator)
            if not av:
                raise MaKaCError(_("You could not login through SSO."))
            self._setSessionVars(av)
            self._redirect(self._url)
        elif self._authId:
            session['Authenticator'] = self._authId
            if self._returnURL:
                session['loginReturnURL'] = self._returnURL
            self._redirect(str(urlHandlers.UHSignInSSO.getURL(authId=self._authId)))
        else:
            raise MaKaCError(_("You did not pass the authenticator"))


class RHSignOut(base.RH):

    _isMobile = False

    def _checkParams(self, params):
        self._returnURL = params.get("returnURL", str(urlHandlers.UHWelcome.getURL())).strip()

    def _process(self):
        if self._getUser():
            self._returnURL = AuthenticatorMgr().getLogoutCallbackURL(self) or self._returnURL
            self._setUser(None)
        session.clear()
        self._redirect(self._returnURL)


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
            av_list = AvatarHolder().match({"email": self._email}, exact=1)
            if not av_list:
                raise NoReportError(_("We couldn't find any account with this email address"))
            av = av_list[0]
        if av:
            mail.send_login_info(av)
        self._redirect(urlHandlers.UHSignIn.getURL())


class RHResetPasswordBase:
    _isMobile = False
    _token_storage = GenericCache('resetpass')

    def _checkParams(self, params):
        self._token = request.view_args['token']
        self._data = self._token_storage.get(self._token)
        if not self._data:
            raise NoReportError(_('Invalid token. It might have expired.'))
        self._avatar = AuthenticatorMgr().getById(self._data['tag']).getAvatarByLogin(self._data['login'])
        self._identity = self._avatar.getIdentityById(self._data['login'], self._data['tag'])
        if not self._identity:
            raise NoReportError(_('Invalid token (no login found)'))

    def _checkParams_POST(self):
        self._password = request.form['password'].strip()
        if not self._password:
            raise FormValuesError(_('Your password must not be empty.'))
        if self._password != request.form['password_confirm'].strip():
            raise FormValuesError(_('Your password confirmation is not correct.'))

    def _process_GET(self):
        return self._getWP().display()

    def _process_POST(self):
        self._identity.setPassword(self._password.encode('utf-8'))
        self._token_storage.delete(self._token)
        url = self._getRedirectURL()
        url.addParam('passwordChanged', True)
        self._redirect(url)


class RHResetPassword(RHResetPasswordBase, base.RH):
    def _getRedirectURL(self):
        return urlHandlers.UHSignIn.getURL()

    def _getWP(self):
        return signIn.WPResetPassword(self)


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
