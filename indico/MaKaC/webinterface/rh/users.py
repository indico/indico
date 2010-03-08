# -*- coding: utf-8 -*-
##
## $Id: users.py,v 1.43 2009/06/04 09:30:00 jose Exp $
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

import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.rh.admins as admins
import MaKaC.webinterface.pages.personalization as personalization
import MaKaC.webinterface.pages.admins as adminPages
import MaKaC.user as user
import MaKaC.common.info as info
import MaKaC.errors as errors
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.mail as mail
import MaKaC.common.indexes as indexes
from MaKaC.common.general import *
from MaKaC.errors import MaKaCError, ModificationError
from MaKaC.accessControl import AdminList
from MaKaC.webinterface.rh.base import RH, RHProtected
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.common import DBMgr
from MaKaC.common import pendingQueues
import MaKaC.common.timezoneUtils as timezoneUtils
import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
import re
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

class RHUserManagementLogMeAs( admins.RHAdminBase ):
    
    def _checkParams( self, params ):
        admins.RHAdminBase._checkParams( self, params )
        self._params = params
        self._userId = None
        self._av = None
        
        self._returnURL = urlHandlers.UHWelcome.getURL()
        if "returnURL" in params.keys():
            self._returnURL = params["returnURL"]
        
        if "selectedPrincipals" in params.keys() and not "cancel" in params:
            self._userId = params["selectedPrincipals"]
            try:
                self._av = user.AvatarHolder().getById(self._userId)
            except:
                raise MaKaCError("can't found user with id %s"%self._userId)
    
    def _process( self ):
        if self._av:
            tzUtil = timezoneUtils.SessionTZ(self._av)
            tz = tzUtil.getSessionTZ()
            self._getSession().setVar("ActiveTimezone",tz)
            self._getSession().setUser(self._av)
            self._redirect(self._returnURL)
        else:
            p = adminPages.WPSelectUserToLogAs( self )
            return p.display(**self._getRequestParams())


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
        ih = AuthenticatorMgr()
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
                self._params["msg"] += _("You must enter the same password two time.")+"<br>"
                save = False
            if not ih.isLoginFree(self._params.get("login","")):
                self._params["msg"] += _("Sorry, the login you requested is already in use. Please choose another one.")+"<br>"
                save = False
            if not self._validMail(self._params.get("email","")):
                self._params["msg"]+= _("You must enter a valid email adress")
                save = False
        if save:
            #Data are OK, Now check if there is an existing user or create a new one
            ah = user.AvatarHolder()
            res =  ah.match({"email": self._params["email"]}, exact=1, forceWithoutExtAuth=True)
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
                    id = ih.createIdentity( li, a, "Local" )
                    ih.add( id )
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
                id = ih.createIdentity( li, a, "Local" )
                ih.add( id )
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


#class RHUserModify( RHProtected ):
#    
#    def _checkProtection( self ):
#        if self._getUser() and ( (not self._getUser() in AdminList.getInstance().getList()) or (self._av != self._getUser()) ):
#            raise errors.AccessError("User Modification")
#        RHProtected._checkProtection( self )
#    
#    def _checkParams( self, params ):
#        self._av = user.AvatarHolder().getById(params["userId"])
#    
#    def _process( self ):
#        p = users.WPUserModify( self, self._av )
#        return p.display()


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
    
    def setUserData( self, a, userData):
        a.setName( userData["name"] )
        a.setSurName( userData["surName"] )
        a.setTitle( userData["title"] )
        a.setOrganisation( userData["organisation"] )
        a.setLang( userData["lang"] )
        a.setAddress( userData["address"] )
        a.setEmail( userData["email"] )
        a.setSecondaryEmails( userData.get("secEmails", [] ))
        a.setTelephone( userData["telephone"] )
        a.setFax( userData["fax"] )

        #################################
        # Fermi timezone awareness      #
        #################################

        a.setTimezone(userData["timezone"])
        a.setDisplayTZMode(userData["displayTZMode"])

        #################################
        # Fermi timezone awareness(end) #
        #################################

    setUserData = classmethod( setUserData )


class RHUserBase( RHProtected ):
    
    def _checkParams( self, params ):
        if "userId" not in params or params["userId"].strip() == "":
            raise MaKaCError( _("user id not specified"))
        ah = user.AvatarHolder()
        self._target = self._avatar = ah.getById( params["userId"] )        
    
    def _checkProtection( self ):
        
        RHProtected._checkProtection( self )
        if not self._avatar.canUserModify( self._getUser() ):
            raise ModificationError("user")        


class RHUserDetails( RHUserBase):
    _uh = urlHandlers.UHUserDetails
    
    def _checkProtection( self ):
        RHUserBase._checkProtection( self )
        if self._aw.getUser():
            if not self._avatar.canModify( self._aw ):
                raise errors.AccessControlError("user")             
    
    def _process( self ):
        p = adminPages.WPUserDetails( self, self._avatar )
        return p.display()
    
    
class RHUserBaskets( base.RHProtected ):
    _uh = urlHandlers.UHUserBaskets
    
    def _process( self ):
        p = adminPages.WPUserBaskets( self, self._getUser() )
        return p.display()

class RHUserPreferences( base.RHProtected ):
    _uh = urlHandlers.UHUserPreferences
    
    def _process( self ):
        p = adminPages.WPUserPreferences( self, self._getUser() )
        return p.display()


class RHUserPersBase( base.RHDisplayBaseProtected ):

    def _checkParams( self, params ):
        base.RHDisplayBaseProtected._checkParams(self, params)

    def _checkProtection( self ):
        RHProtected._checkSessionUser( self )
        if not self._aw.getUser():
            raise errors.AccessControlError("user")             

class RHUserEvents(RHUserPersBase):
    _uh = urlHandlers.UHGetUserEventPage
    
    def _process( self ):
        p = personalization.WPDisplayUserEvents( self )
        return p.display()

class RHUserModification( RHUserBase ):
    _uh = urlHandlers.UHUserModification

    def _checkParams( self, params ):
        self._params = params
        self._cancel = False
        if params.get("cancel", ""):
            self._cancel = True
        RHUserBase._checkParams( self, params )
        self._save = params.get("Save", "")
        self._addEmail = params.get("addSecEmail", "")
        self._removeEmail = params.get("removeSecEmail", "")
        
    def _process( self ):
        if self._cancel:
            self._redirect(urlHandlers.UHUserDetails.getURL(self._avatar))
            return
        save = False
        self._params["msg"] = ""
        if self._save:
            save = True
            #check submited data
            if not self._params.get("name",""):
                self._params["msg"] += "You must enter a name.<br>"
                save = False
            if not self._params.get("surName",""):
                self._params["msg"] += "You must enter a surname.<br>"
                save = False
            if not self._params.get("organisation",""):
                self._params["msg"] += "You must enter the name of your organisation.<br>"
                save = False
            if not self._params.get("email",""):
                self._params["msg"] += "You must enter an email address.<br>"
                save = False
        if self._params.get("email","") != self._avatar.getEmail():
                av = user.AvatarHolder().match({"email": self._params.get("email","")}, forceWithoutExtAuth=True)
                if av:
                    if av[0] != self._avatar:
                        self._params["msg"] += "This email is already used"
                        save = False
        if save:
            #Data are OK, save them
            idxs = indexes.IndexesHolder()
            org = idxs.getById( 'organisation' )
            email = idxs.getById( 'email' )
            name = idxs.getById( 'name' )
            surName = idxs.getById( 'surName' )
            org.unindexUser(self._avatar)
            email.unindexUser(self._avatar)
            name.unindexUser(self._avatar)
            surName.unindexUser(self._avatar)
            self._params["secEmails"] = self._normaliseListParam(self._params.get("secEmails",[]))
            _UserUtils.setUserData( self._avatar, self._params )
            self._getSession().setLang(self._avatar.getLang())
            org.indexUser(self._avatar)
            email.indexUser(self._avatar)
            name.indexUser(self._avatar)
            surName.indexUser(self._avatar)
            
            #----Grant rights if anything
            ph=pendingQueues.PendingQueuesHolder()
            ph.grantRights(self._avatar)
            #-----
            websession = self._aw.getSession()
            tzUtil = timezoneUtils.SessionTZ(self._aw.getUser())
            tz = tzUtil.getSessionTZ()
            websession.setVar("ActiveTimezone",tz) 
            self._redirect(urlHandlers.UHUserDetails.getURL(self._avatar))
            
        elif self._addEmail:
            self._params["secEmails"] = self._normaliseListParam(self._params.get("secEmails",[]))
            email = self._params.get("secEmailAdd", "")
            av = user.AvatarHolder().match({"email": email}, exact=1, forceWithoutExtAuth=True)
            add = True
            if av:
                if av[0] != self._avatar:
                    self._params["msg"] += "This email is already used"
                    add = False
            if email and add and not email in self._params["secEmails"]:
                self._params["secEmails"].append(email)
            p = adminPages.WPUserModification( self, self._avatar, self._params )
            return p.display()
        elif self._removeEmail:
            
            emails = self._normaliseListParam(self._params.get("secEmailRemove",[]))
            self._params["secEmails"] = self._normaliseListParam(self._params["secEmails"])
            for email in emails:
                if email and email in self._params["secEmails"]:
                    self._params["secEmails"].remove(email)
            p = adminPages.WPUserModification( self, self._avatar, self._params )
            websession = self._aw.getSession()
            tzUtil = timezoneUtils.SessionTZ(self._aw.getUser())
            tz = tzUtil.getSessionTZ()
            websession.setVar("ActiveTimezone",tz) 
            return p.display()
        else:
            p = adminPages.WPUserModification( self, self._avatar, self._params )
            websession = self._aw.getSession()
            tzUtil = timezoneUtils.SessionTZ(self._aw.getUser())
            tz = tzUtil.getSessionTZ()
            websession.setVar("ActiveTimezone",tz) 
            return p.display()
        """
        p = adminPages.WPUserModification( self, self._avatar )
        return p.display()
        """


class RHUserActive( RHUserBase ):
    
    def _checkProtection( self ):
        al = AdminList.getInstance()
        if not (self._aw.getUser() in al.getList()):
            raise errors.AccessError("user status")
    
    def _process( self ):
        self._avatar.activateAccount()
        #----Grant rights if anything
        ph=pendingQueues.PendingQueuesHolder()
        ph.grantRights(self._avatar)
        #-----
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getModerateAccountCreation():
            mail.sendAccountActivated(self._avatar).send()
        self._redirect(urlHandlers.UHUserDetails.getURL(self._avatar))

#class RHUserPerformModification( RHUserBase ):
#    _uh = urlHandlers.UHUserPerformModification
#    
#    def _checkParams( self, params ):
#        RHUserBase._checkParams( self, params )
#        self._userData = params
#    
#    def _process( self ):
#        _UserUtils.setUserData( self._avatar, self._userData )
#        self._redirect( urlHandlers.UHUserDetails.getURL( self._avatar ) )


class RHUserIdentityBase( RHUserBase ):
    
    def _checkProtection( self ):
        if self._avatar.getIdentityList() == []:
            return 
        RHUserBase._checkProtection( self )
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
    
    def _process( self ):
        
        if self._params.get("Cancel",None) is not None :            
            p = adminPages.WPUserDetails( self, self._avatar )
            return p.display()
            
        msg = ""
        ok = False
        if self._ok:
            ok = True
            ih = AuthenticatorMgr()
            #first, check if login is free
            if not ih.isLoginFree(self._login):
                msg += "Sorry, the login you requested is already in use. Please choose another one.<br>"
                ok = False
            if not self._pwd:
                msg += "you must enter a password<br>"
                ok = False
            #then, check if password is OK
            if self._pwd != self._pwdBis:
                msg += "You must enter the same password two time<br>"
                ok = False
            if ok:
                #create the indentity
                li = user.LoginInfo( self._login, self._pwd )   
                id = ih.createIdentity( li, self._avatar, self._system )
                ih.add( id )
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
        ih = AuthenticatorMgr()
        #first, check if login is free
        if not ih.isLoginFree(self._login):
            self._redirect(self._fromURL + "&msg=Login not avaible")
            return
        #then, check if password is OK
        if self._pwd != self._pwdBis:
            self._redirect(self._fromURL + "&msg=You must enter the same password two time")
            return
        #create the indentity
        li = user.LoginInfo( self._login, self._pwd )   
        id = ih.createIdentity( li, self._avatar, self._system )
        ih.add( id )
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
    
    def _process( self ):                
        if self._params.get("OK",None) is not None :                        
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
            p = adminPages.WPUserDetails( self, self._avatar )
            return p.display()
        elif self._params.get("Cancel",None) is not None :
            p = adminPages.WPUserDetails( self, self._avatar )
            return p.display()
            
        self._params["msg"] = ""
        p = adminPages.WPIdentityChangePassword( self, self._avatar, self._params )        
        return p.display()


class RHUserRemoveIdentity( RHUserIdentityBase ):
    
    def _checkParams( self, params ):
        RHUserIdentityBase._checkParams( self, params )
        self._identityList = self._normaliseListParam(params.get("selIdentities",[]))
    
    def _process( self ):
        am = AuthenticatorMgr()
        for id in self._identityList:
            identity = am.getIdentityById(id)
            am.removeIdentity(identity)
            self._avatar.removeIdentity(identity)
        self._redirect( urlHandlers.UHUserDetails.getURL( self._avatar ) )

class RHCreateExternalUsers(RH):
    _uh = urlHandlers.UHUserSearchCreateExternalUser
    
    def _checkProtection( self ):
        pass
    
    def _checkParams( self, params ):
        from copy import copy
        self._params = copy(params)
        RH._checkParams( self, params )
        self._addURL = ""
        if self._params.has_key( "addURL" ):
            self._addURL = self._params["addURL"]
            del self._params["addURL"]        
        self._identityList = self._normaliseListParam(self._params.get("selectedPrincipals",[]))
        if self._params.has_key("selectedPrincipals"):
            del self._params["selectedPrincipals"]
                    
    def _process( self ):
        from MaKaC.common.Configuration import Config
        from MaKaC.externUsers import ExtUserHolder
        from urllib import urlencode
        euh = ExtUserHolder()
        ah = user.AvatarHolder()
        newIdentityList = []
        for id in self._identityList:
            newId = id
            for authId in Config.getInstance().getAuthenticatorList():
                if id[:len(authId)] == authId:
                    dict = euh.getById(authId).getById(id.split(':')[1])
                    av = user.Avatar(dict)
                    newId = ah.add(av)
                    identity = dict["identity"](dict["login"], av)
                    try:
                        dict["authenticator"].add(identity)
                    except:
                        pass
                    av.activateAccount()
            newIdentityList.append("selectedPrincipals=%s"%newId)
        if self._addURL.find("?") != -1:
            targetURL = self._addURL + "&" + urlencode(self._params) + "&" + "&".join(newIdentityList)
        else:
            targetURL = self._addURL + "?" + urlencode(self._params) + "&" + "&".join(newIdentityList)
        self._redirect( targetURL )



    
