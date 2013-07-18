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

import re
from flask import session

import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.rh.admins as admins
import MaKaC.webinterface.pages.admins as adminPages
import MaKaC.user as user
import MaKaC.common.info as info
import MaKaC.errors as errors
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.mail as mail
from MaKaC.errors import MaKaCError, NotFoundError
from MaKaC.accessControl import AdminList
from MaKaC.webinterface.rh.base import RH, RHProtected
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.common import DBMgr
from MaKaC.common import pendingQueues
from MaKaC.i18n import _


class RHUserManagementSwitchAuthorisedAccountCreation( admins.RHAdminBase ):

    def _process( self ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        minfo.setAuthorisedAccountCreation(not minfo.getAuthorisedAccountCreation())
        self._redirect(urlHandlers.UHUserManagement.getURL())

class RHUserManagementSwitchNotifyAccountCreation( admins.RHAdminBase ):

    def _process( self ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        minfo.setNotifyAccountCreation(not minfo.getNotifyAccountCreation())
        self._redirect(urlHandlers.UHUserManagement.getURL())

class RHUserManagementSwitchModerateAccountCreation( admins.RHAdminBase ):

    def _process( self ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        minfo.setModerateAccountCreation(not minfo.getModerateAccountCreation())
        self._redirect(urlHandlers.UHUserManagement.getURL())

class RHUserManagement( admins.RHAdminBase ):

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        p = adminPages.WPUserManagement( self, self._params )
        return p.display()

class RHUsers( admins.RHAdminBase ):

    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        p = adminPages.WPUserList( self, self._params )
        return p.display()


class RHUserCreation( RH ):
    _uh = urlHandlers.UHUserCreation

    def _checkProtection( self ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if self._aw.getUser() and self._aw.getUser() in minfo.getAdminList().getList():
            return
        if not minfo.getAuthorisedAccountCreation():
            raise MaKaCError( _("User registration has been disabled by the site administrator"))

    def _checkParams( self, params ):
        self._params = params
        RH._checkParams( self, params )
        self._save = params.get("Save", "")

    def _process( self ):
        save = False
        authManager = AuthenticatorMgr.getInstance()
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        self._params["msg"] = ""
        if self._save:
            save = True
            #check submited data
            if not self._params.get("name",""):
                self._params["msg"] += _("You must enter a name.")+"<br>"
                save = False
            if not self._params.get("surName",""):
                self._params["msg"] += _("You must enter a surname.")+"<br>"
                save = False
            if not self._params.get("organisation",""):
                self._params["msg"] += _("You must enter the name of your organisation.")+"<br>"
                save = False
            if not self._params.get("email",""):
                self._params["msg"] += _("You must enter an email address.")+"<br>"
                save = False
            if not self._params.get("login",""):
                self._params["msg"] += _("You must enter a login.")+"<br>"
                save = False
            if not self._params.get("password",""):
                self._params["msg"] += _("You must define a password.")+"<br>"
                save = False
            if self._params.get("password","") != self._params.get("passwordBis",""):
                self._params["msg"] += _("You must enter the same password twice.")+"<br>"
                save = False
            if not authManager.isLoginAvailable(self._params.get("login", "")):
                self._params["msg"] += _("Sorry, the login you requested is already in use. Please choose another one.")+"<br>"
                save = False
            if not self._validMail(self._params.get("email","")):
                self._params["msg"]+= _("You must enter a valid email address")
                save = False
        if save:
            #Data are OK, Now check if there is an existing user or create a new one
            ah = user.AvatarHolder()
            res =  ah.match({"email": self._params["email"]}, exact=1, searchInAuthenticators=False)
            if res:
                #we find a user with the same email
                a = res[0]
                #check if the user have an identity:
                if a.getIdentityList():
                    self._redirect( urlHandlers.UHUserExistWithIdentity.getURL(a))
                    return
                else:
                    #create the identity to the user and send the comfirmatio email
                    _UserUtils.setUserData( a, self._params )
                    li = user.LoginInfo( self._params["login"], self._params["password"] )
                    id = authManager.createIdentity( li, a, "Local" )
                    authManager.add( id )
                    DBMgr.getInstance().commit()
                    if minfo.getModerateAccountCreation():
                        mail.sendAccountCreationModeration(a).send()
                    else:
                        mail.sendConfirmationRequest(a).send()
                        if minfo.getNotifyAccountCreation():
                            mail.sendAccountCreationNotification(a).send()
            else:
                a = user.Avatar()
                _UserUtils.setUserData( a, self._params )
                ah.add(a)
                li = user.LoginInfo( self._params["login"], self._params["password"] )
                id = authManager.createIdentity( li, a, "Local" )
                authManager.add( id )
                DBMgr.getInstance().commit()
                if minfo.getModerateAccountCreation():
                    mail.sendAccountCreationModeration(a).send()
                else:
                    mail.sendConfirmationRequest(a).send()
                    if minfo.getNotifyAccountCreation():
                        mail.sendAccountCreationNotification(a).send()
            self._redirect(urlHandlers.UHUserCreated.getURL( a ))
        else:
            cp=None
            if self._params.has_key("cpEmail"):
                ph=pendingQueues.PendingQueuesHolder()
                cp=ph.getFirstPending(self._params["cpEmail"])
            if self._aw.getUser() and self._aw.getUser() in minfo.getAdminList().getList():
                p = adminPages.WPUserCreation( self, self._params, cp )
            else:
                p = adminPages.WPUserCreationNonAdmin( self, self._params, cp )
            return p.display()

    def _validMail(self,email):
        if re.search("^[a-zA-Z][\w\.-]*[a-zA-Z0-9]@[a-zA-Z0-9][\w\.-]*[a-zA-Z0-9]\.[a-zA-Z][a-zA-Z\.]*[a-zA-Z]$",email):
            return True
        return False

class RHUserCreated( RH ):

    def _checkParams( self, params ):
        self._av = user.AvatarHolder().getById(params["userId"])

    def _process( self ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if self._aw.getUser() and self._aw.getUser() in minfo.getAdminList().getList():
            p = adminPages.WPUserCreated( self, self._av )
        else:
            p = adminPages.WPUserCreatedNonAdmin( self, self._av )
        return p.display()


class RHUserExistWithIdentity( RH ):

    def _checkParams( self, params ):
        self._av = user.AvatarHolder().getById(params["userId"])

    def _process( self ):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if self._aw.getUser() and self._aw.getUser() in minfo.getAdminList().getList():
            p = adminPages.WPUserExistWithIdentity( self, self._av )
        else:
            p = adminPages.WPUserExistWithIdentityNonAdmin( self, self._av )
        return p.display()


class _UserUtils:

    def setUserData(self, a, userData, reindex=False):
        a.setName( userData["name"], reindex=reindex )
        a.setSurName( userData["surName"], reindex=reindex )
        a.setTitle( userData["title"] )
        a.setOrganisation( userData["organisation"], reindex=reindex )
        if userData.has_key("lang"):
            a.setLang( userData["lang"] )
        a.setAddress( userData["address"] )
        a.setEmail( userData["email"], reindex )
        a.setSecondaryEmails( userData.get("secEmails", [] ))
        a.setTelephone( userData["telephone"] )
        a.setFax( userData["fax"] )
        if userData.has_key("showPastEvents"):
            a.getPersonalInfo().setShowPastEvents( userData.has_key("showPastEvents"))

        #################################
        # Fermi timezone awareness      #
        #################################
        if userData.has_key("timezone"):
            a.setTimezone(userData["timezone"])
        if userData.has_key("displayTZMode"):
            a.setDisplayTZMode(userData["displayTZMode"])

        #################################
        # Fermi timezone awareness(end) #
        #################################

    setUserData = classmethod( setUserData )


class RHUserBase(RHProtected):
    def _checkParams(self, params):
        if not session.user:
            # Let checkProtection deal with it.. no need to raise an exception here
            # if no user is specified
            return

        if not params.setdefault('userId', session.get('_avatarId')):
            raise MaKaCError(_("user id not specified"))

        ah = user.AvatarHolder()
        self._target = self._avatar = ah.getById(params['userId'])
        if self._avatar is None:
            raise NotFoundError("The user id does not match any existing user.")

    def _checkProtection(self):
        RHProtected._checkProtection(self)
        if not self._doProcess:
            # Logged-in check failed
            return
        if not self._avatar.canUserModify(self._getUser()):
            raise errors.AccessControlError("user")


class RHUserDashboard(RHUserBase):
    _uh = urlHandlers.UHUserDashboard

    def __init__(self, req):
        RHUserBase.__init__(self, req)

    def _process(self):
        p = adminPages.WPUserDashboard(self, self._avatar)
        return p.display()


class RHUserDetails( RHUserBase):
    _uh = urlHandlers.UHUserDetails

    def _process( self ):
        p = adminPages.WPUserDetails( self, self._avatar )
        return p.display()

class RHUserBaskets( RHUserBase ):
    _uh = urlHandlers.UHUserBaskets

    def _checkProtection( self ):
        RHUserBase._checkProtection( self )
        if self._aw.getUser():
            if not self._avatar.canModify( self._aw ):
                raise errors.AccessControlError("user")

    def _process( self ):
        p = adminPages.WPUserBaskets( self, self._avatar )
        return p.display()

class RHUserPreferences( RHUserBase ):
    _uh = urlHandlers.UHUserPreferences

    def _checkProtection( self ):
        RHUserBase._checkProtection( self )
        if self._aw.getUser():
            if not self._avatar.canModify( self._aw ):
                raise errors.AccessControlError("user")

    def _process( self ):
        p = adminPages.WPUserPreferences( self, self._avatar )
        return p.display()

class RHUserPersBase( base.RHDisplayBaseProtected ):

    def _checkParams( self, params ):
        base.RHDisplayBaseProtected._checkParams(self, params)

    def _checkProtection( self ):
        RHProtected._checkSessionUser( self )
        if not self._aw.getUser():
            raise errors.AccessControlError("user")

class RHUserActive( RHUserBase ):

    def _checkProtection( self ):
        al = AdminList.getInstance()
        if not (self._aw.getUser() in al.getList()):
            raise errors.AccessError("user status")

    def _process( self ):
        self._avatar.activateAccount()
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getModerateAccountCreation():
            mail.sendAccountActivated(self._avatar).send()
        self._redirect(urlHandlers.UHUserDetails.getURL(self._avatar))

class RHUserDisable( RHUserBase ):

    def _checkProtection( self ):
        al = AdminList.getInstance()
        if not (self._aw.getUser() in al.getList()):
            raise errors.AccessError("user status")

    def _process( self ):
        self._avatar.disabledAccount()
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getModerateAccountCreation():
            mail.sendAccountDisabled(self._avatar).send()
        self._redirect(urlHandlers.UHUserDetails.getURL(self._avatar))


class RHUserIdentityBase( RHUserBase ):

    def _checkProtection(self):
        RHUserBase._checkProtection(self)
        if not self._doProcess:
            return False
        if not self._avatar.getIdentityList():
            return
        if not self._avatar.canModify( self._aw ):
            raise errors.ModificationError("user")


class RHUserIdentityCreation( RHUserIdentityBase ):
    _uh = urlHandlers.UHUserIdentityCreation

    def _checkParams( self, params ):
        RHUserIdentityBase._checkParams( self, params )
        self._login = params.get("login", "")
        self._pwd = params.get("password", "")
        self._pwdBis = params.get("passwordBis", "")
        self._system = params.get("system", "")
        self._ok = params.get("OK", "")
        self._params = params

    def _process(self):
        if self._params.get("Cancel") is not None:
            self._redirect(urlHandlers.UHUserDetails.getURL(self._avatar))
            return

        msg = ""
        if self._ok:
            ok = True
            authManager = AuthenticatorMgr.getInstance()
            #first, check if login is free
            if not authManager.isLoginAvailable(self._login):
                msg += "Sorry, the login you requested is already in use. Please choose another one.<br>"
                ok = False
            if not self._pwd:
                msg += "you must enter a password<br>"
                ok = False
            #then, check if password is OK
            if self._pwd != self._pwdBis:
                msg += "You must enter the same password twice<br>"
                ok = False
            if ok:
                #create the indentity
                li = user.LoginInfo( self._login, self._pwd )
                id = authManager.createIdentity( li, self._avatar, self._system )
                authManager.add( id )
                self._redirect( urlHandlers.UHUserDetails.getURL( self._avatar ) )
                return

        self._params["msg"] = msg
        p = adminPages.WPIdentityCreation( self, self._avatar, self._params )
        return p.display()



class RHUserIdPerformCreation( RHUserIdentityBase ):
    _uh = urlHandlers.UHUserIdPerformCreation

    def _checkParams( self, params ):
        RHUserIdentityBase._checkParams( self, params )
        self._login = params.get("login", "")
        self._pwd = params.get("password", "")
        self._pwdBis = params.get("passwordBis", "")
        self._fromURL = params.get("fromURL", "")
        self._system = params.get("system", "")

    def _process( self ):
        authManager = AuthenticatorMgr.getInstance()
        #first, check if login is free
        if not authManager.isLoginAvailable(self._login):
            self._redirect(self._fromURL + "&msg=Login not avaible")
            return
        #then, check if password is OK
        if self._pwd != self._pwdBis:
            self._redirect(self._fromURL + "&msg=You must enter the same password twice")
            return
        #create the indentity
        li = user.LoginInfo( self._login, self._pwd )
        id = authManager.createIdentity( li, self._avatar, self._system )
        authManager.add( id )
        #commit and if OK, send activation mail
        DBMgr.getInstance().commit()
        scr = mail.sendConfirmationRequest(self._avatar)
        scr.send()
        self._redirect( urlHandlers.UHUserDetails.getURL( self._avatar ) ) #to set to the returnURL


class RHUserIdentityChangePassword( RHUserIdentityBase ):
    _uh = urlHandlers.UHUserIdentityChangePassword

    def _checkParams( self, params ):
        RHUserIdentityBase._checkParams( self, params )
        self._params = params

    def _process(self):
        if self._params.get("OK") is not None:
            if self._params.get("password","") == "" or self._params.get("passwordBis","") == "" :
                self._params["msg"] = _("Both password and password confirmation fields must be filled up")
                del self._params["OK"]
                p = adminPages.WPIdentityChangePassword( self, self._avatar, self._params )
                return p.display()
            if self._params.get("password","") != self._params.get("passwordBis","") :
                self._params["msg"] = _("Password and password confirmation are not equal")
                del self._params["OK"]
                p = adminPages.WPIdentityChangePassword( self, self._avatar, self._params )
                return p.display()
            identity = self._avatar.getIdentityById(self._params["login"], "Local")
            identity.setPassword(self._params["password"])
            self._redirect(urlHandlers.UHUserDetails.getURL(self._avatar))
        elif self._params.get("Cancel") is not None:
            self._redirect(urlHandlers.UHUserDetails.getURL(self._avatar))
        else:
            self._params["msg"] = ""
            p = adminPages.WPIdentityChangePassword(self, self._avatar, self._params)
            return p.display()


class RHUserRemoveIdentity( RHUserIdentityBase ):

    def _checkParams( self, params ):
        RHUserIdentityBase._checkParams( self, params )
        self._identityList = self._normaliseListParam(params.get("selIdentities",[]))

    def _process( self ):
        authManager = AuthenticatorMgr.getInstance()
        for i in self._identityList:
            identity = authManager.getIdentityById(i)
            if len(identity.getUser().getIdentityList()) > 1:
                authManager.removeIdentity(identity)
                self._avatar.removeIdentity(identity)
        self._redirect( urlHandlers.UHUserDetails.getURL( self._avatar ) )
