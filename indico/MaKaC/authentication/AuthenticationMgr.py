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
from flask import session

from indico.core.config import Config
from MaKaC.errors import MaKaCError

from indico.util.importlib import import_module

class AuthenticatorMgr:

    def __init__(self):
        self._authenticator_list = []
        for auth, config in Config.getInstance().getAuthenticatorList():
            try:
                mod = import_module("MaKaC.authentication." + auth + "Authentication")
                self._authenticator_list.append(getattr(mod, auth + "Authenticator")())
            except ImportError:
                raise MaKaCError("Impossible to load %s" % auth)

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
                    if auth.canUserBeActivated():
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

        if auth is None:
            # search all authenticators
            authList = self.getList()
        else:
            # get the actual Authenticator objects
            authList = map(self.getById, auth)

        # we search for Avatars in each authenticator
        foundAvatars = {}
        for auth in authList:
            try:
                avatar = auth.getAvatarByLogin(login)
                foundAvatars[auth.getId().strip()] = avatar
            except KeyError:
                pass

        return foundAvatars

    def isLoginAvailable(self, login):
        for au in self.getList():
            try:
                if au.getById(login):
                    return False
            except KeyError,e:
                pass
        return True

    def getDefaultAuthenticator(self):
        return self.getList()[0]

    def getList(self):
        return self._authenticator_list

    def getAuthenticatorIdList(self):
        return [auth.getId() for auth in self._authenticator_list]

    def hasExternalAuthenticators(self):
        for auth in self.getList():
            if auth.getId() != 'Local':
                return True
        return False

    def createIdentity(self, li, avatar, system=""):
        auth = self.getById( system )
        if not auth:
            auth = self.getDefaultAuthenticator()
        return auth.createIdentity(li, avatar)

    def removeIdentity(self, identity):
        #check if there is almost another one identity
        if len(identity.getUser().getIdentityList()) > 1:
            auth = self.getById(identity.getAuthenticatorTag())
            auth.remove(identity)

    def getIdentityById(self, id):
        for auth in self.getList():
            try:
                identity = auth.getById(id)
                if identity:
                    return identity
            except KeyError,e:
                pass
        return None

    def isSSOLoginActive(self):
        for auth in self.getList():
            if auth.isSSOLoginActive():
                return True
        return False

    def SSOLogin(self, rh, authId):
        auth = self.getById( authId )
        if auth and auth.isSSOLoginActive():
            av = auth.retrieveAvatar(rh)
            if av:
                session["SSOLogin"] = auth.getId()
                return av
        return None

    def getLogoutCallbackURL(self, rh):
        authId = session.pop('SSOLogin', None)
        if authId:
            auth = self.getById(authId)
            return auth.getLogoutCallbackURL()
