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

from MaKaC.common.general import *

from MaKaC.common.Configuration import Config
from MaKaC.authentication.LocalAuthentication import LocalAuthenticator



class AuthenticatorMgr:
    
    def __init__(self):
        
        self.AuthenticatorList = []
        config = Config.getInstance()
        for  auth in config.getAuthenticatorList():
            if auth == "Local":
                self.AuthenticatorList.append( LocalAuthenticator() )
            if auth == "Nice":
                from MaKaC.authentication.NiceAuthentication import NiceAuthenticator
                self.AuthenticatorList.append( NiceAuthenticator() )
        self.create = True
    
    
    def add( self, newId):
        auth = self.getById( newId.getAuthenticatorTag() )
        auth.add( newId )

    def getById( self, id ):
        for auth in self.AuthenticatorList:
            if auth.getId() == id.strip():
                return auth
        return None

    def getAvatar( self, li , authenticator=None, create=None):
        if authenticator:
            auth = self.getById(authenticator)
            try:
                return auth.getAvatar( li )
            except KeyError, e:
                pass
        else:
            for auth in self.AuthenticatorList:
                try:
                    valid=auth.getAvatar( li )
                    if valid:
                        return valid
                except KeyError, e:
                    pass
            # The authentication failed. If create, check if we can create the user automaticaly
            if self.create:
                #check if the login is OK with Authenticator which can create a user
                for auth in self.AuthenticatorList:
                    if auth.getUserCreator():
                        user = auth.getUserCreator().create(li)
                        if user != None:
                            if auth.getId().strip() == 'Nice':
                                user.activateAccount()
                            return user
        return None
    
    def isLoginFree( self, login):
        for au in self.AuthenticatorList:
            try:
                if au.getById(login):
                    return False
            except KeyError,e:
                pass
        return True
    
    def _getDefaultAuthenticator( self ):
        return self.AuthenticatorList[0]    
    
    def getList(self):
        return self.AuthenticatorList

    def createIdentity(self, li, avatar, system=""):
        auth = self.getById( system )
        if not auth:
            auth = self._getDefaultAuthenticator()
        return auth.createIdentity(li, avatar)
    
    def removeIdentity( self, Id):
        #check if there is almost another one identity
        if len(Id.getUser().getIdentityList()) > 1:
            auth = self.getById(Id.getAuthenticatorTag())
            auth.remove(Id)
    
    def getIdentityById(self, id):
        for auth in self.AuthenticatorList:
            try:
                Id = auth.getById(id)
                if Id:
                    return Id
            except KeyError,e:
                pass
        return None

    def autoLogin(self, rh):
        #Try to login from request handler
        i = 0
        for auth in self.AuthenticatorList:
            av = auth.autoLogin(rh)
            if av:
                rh._getSession().setVar("autoLogin", auth.getId())
                return av
        return None
    
    def autoLogout(self, rh):
        authId = rh._getSession().getVar("autoLogin")
        if authId:
            rh._getSession().removeVar("autoLogin")
            auth = self.getById(authId)
            return auth.autoLogout(rh)

    
