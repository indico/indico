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

from MaKaC.common.Configuration import Config
from MaKaC.errors import MaKaCError

class AuthenticatorMgr:

    _instance = None

    def __init__(self):

        self._authenticator_list = []
        config = Config.getInstance()
        for auth in config.getAuthenticatorList():
            try:
                self._authenticator_list.append(getattr(__import__("MaKaC.authentication." + auth + "Authentication", globals(), locals(),[auth + "Authentication"]), auth + "Authenticator")())
            except:
                raise MaKaCError("Impossible to load %s" % auth)

    @classmethod
    def getInstance( cls ):

        if cls._instance == None:
            cls._instance = AuthenticatorMgr()
        return cls._instance

    def add( self, newId):
        auth = self.getById( newId.getAuthenticatorTag() )
        auth.add( newId )

    def getById( self, authId ):
        for auth in self.getList():
            if auth.getId() == authId.strip():
                return auth
        return None

    def getAvatar( self, li , authenticator=None):
        if authenticator:
            auth = self.getById(authenticator)
            return auth.getAvatar( li )
        else:
            for auth in self.getList():
                valid = auth.getAvatar( li )
                if valid:
                    return valid
            #check if the login is OK with Authenticator which can create a user
            for auth in self.getList():
                user = auth.createUser(li)
                if user != None:
                    if auth.getId().strip() == 'Nice':
                        user.activateAccount()
                    return user
        return None

    def getAvatarByLogin(self, login, auth = None):
        """ Returns an Avatar object based on the person's login.
            If authList is set, we will only look in the given authenticators.
            If not set, we will look in all authenticators.
            If we find this login in more than one authenticator, and there is at least 2
            different Avatar objects, we will return a dictionary authenticatorName:Avatar object.
            If nothing is found, we will return None

            :param login: the user login
            :type login: str

            :param auth: a list of names of the authenticators to use, or None
            :type auth: str, list or NoneType
        """

        if auth == None:
            # search all authenticators
            authList = self.getList()
        else:
            # get the actual Authenticator objects
            authList = list(self.getById(a) for a in auth)

        # we search for Avatars in each authenticator
        foundAvatars = {}
        for auth in authList:
            try:
                avatar = auth.getAvatarByLogin(login)
                foundAvatars[auth.getId().strip()] = avatar
            except KeyError:
                pass

        return foundAvatars

    def isLoginFree( self, login):
        for au in self.getList():
            try:
                if au.getById(login):
                    return False
            except KeyError,e:
                pass
        return True

    def _getDefaultAuthenticator( self ):
        return self.getList()[0]

    def getList(self):
        return self._authenticator_list

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
        for auth in self.getList():
            try:
                Id = auth.getById(id)
                if Id:
                    return Id
            except KeyError,e:
                pass
        return None

    def autoLogin(self, rh):
        # Try to login from request handler
        for auth in self.getList():
            av = auth.autoLogin(rh)
            if av:
                session['autoLogin'] = auth.getId()
                return av
        return None

    def autoLogout(self, rh):
        authId = session.pop('autoLogin', None)
        if authId:
            auth = self.getById(authId)
            return auth.autoLogout(rh)
