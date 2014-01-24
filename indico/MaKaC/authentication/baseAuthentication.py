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
from flask import request

from persistent import Persistent

from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.errors import UserError, MaKaCError
from MaKaC.i18n import _
from indico.core.config import Config
from MaKaC.user import LoginInfo

"""
In this file the Authenticator base class is defined, also the PIdentity base.

Every Authenticator that is developed has to overwrite the main methods if they want to have a full functionallity.
"""


class Authenthicator(ObjectHolder):

    def add( self, newId ):
        """ Add a new Id to the ObjectHolder.
            Returns the identity Id.

            :param newId: a PIdentity object that contains the user and login
            :type newId: MaKaC.baseAuthentication.PIdentity child class
        """

        if self.hasKey( newId.getId() ):
            raise UserError( _("identity already exists"))
        id = newId.getId()
        tree = self._getIdx()
        if tree.has_key(id):
            raise UserError
        tree[ id ] = newId
        return id

    def _transformLogin(self, login):
        """Override to convert login names e.g. to lowercase"""
        return login

    def getAvatar(self, li):
        """ Returns an Avatar object, checking that the password is right.

            :param li: a LoginInfo object with the person's login string and password
            :type li: MaKaC.user.LoginInfo
        """

        login = self._transformLogin(li.getLogin())
        if self.hasKey(login):
            identity = self.getById(login)
            avatar = identity.authenticate(li)
            if avatar:
                self._postLogin(login, avatar)
                return avatar
        return None

    def getAvatarByLogin(self, login):
        """ Returns an Avatar object, WITHOUT checking the password!
            Will throw KeyError if not found.

            :param login: the person's login string
            :type login: str
        """
        login = self._transformLogin(login)
        if self.hasKey(login):
            return self.getById(login).getUser()
        return None

    def getIdx(self):
        """ Returns the index of the ObjectHolder
        """
        return self._getIdx()

    @classmethod
    def getId(self):
        """ Returns the Id of the Authenticator
        """
        return self.id

    def getName(self):
        """ Returns the name of the Authenticator. If it is setup in the configuration, otherwise, default name.
        """
        return Config.getInstance().getAuthenticatorConfigById(self.getId()).get("name", self.name)

    def getDescription(self):
        """ Returns the description of the Authenticator.
        """
        return self.description

    def isSSOLoginActive(self):
        """ Returns if Single Sign-on is active
        """
        return Config.getInstance().getAuthenticatorConfigById(self.getId()).get("SSOActive", False)

    def canUserBeActivated(self):
        """ Returns if the Avatar object of the created users are activated by default

            To override
        """
        return False

    def SSOLogin(self, rh):
        """ Returns the Avatar object when the Authenticator makes login trough Single Sign-On

            :param rh: the Request Handler
            :type rh: MaKaC.webinterface.rh.base.RH and subclasses
        """
        return None

    def createIdentity(self, li, avatar):
        """ Returns the created PIdentity object with the LoginInfo an Avatar

            :param li: a LoginInfo object with the person's login string and password
            :type li: MaKaC.user.LoginInfo

            :param avatar: an Avatar object of the user
            :type avatar: MaKaC.user.Avatar
        """
        return None

    def createIdentitySSO(self, login, avatar):
        """Like createIdentity but with just a login (coming from SSO) instead of a login/pw combination."""
        return None

    def fetchIdentity(self, avatar):
        """ Returns the created PIdentity object with the Avatar fetching from the authenticator

            :param avatar: an Avatar object of the user
            :type avatar: MaKaC.user.Avatar
        """
        return None

    def createUser(self, li):
        """ Returns the created Avatar object through an LoginInfo object

            :param li: a LoginInfo object with the person's login string
            :type li: MaKaC.user.LoginInfo
        """
        return None

    def matchUser(self, criteria, exact=0):
        """ Returns the list of users (Avatar) with the given criteria

            :param criteria: the criteria to search
            :type criteria: dict

            :param exact: the match has to be exact
            :type exact: boolean
        """
        return []

    def matchUserFirstLetter(self, index, letter):
        """ Returns the list of users (Avatar) starting by the given letter

            :param index: the index string (name, Surname...)
            :type index: str

            :param letter: the letter char
            :type letter: str
        """
        return []

    def searchUserById(self, id):
        """ Returns an Avatar by the given id

            :param id: the id string
            :type id: str
        """
        return None

    def matchGroup(self, criteria, exact=0):
        """ Returns the list of groups (Group) with the given criteria

            :param criteria: the criteria to search
            :type criteria: dict

            :param exact: the match has to be exact
            :type exact: boolean
        """
        return []

    def matchGroupFirstLetter(self, letter):
        """ Returns the list of groups (Group) starting by the given letter

            :param letter: the letter char
            :type letter: str
        """
        return []

    def getGroupMemberList(self, group):
        """ Returns the list of members (string) for the given group

            :param group: the group string
            :type group: str
        """
        return []

    def isUserInGroup(self, user, group):
        """ Returns True if the user belongs to the group

            :param user: the user string
            :type user: str

            :param group: the group string
            :type group: str
        """
        return False

    def _postLogin(self, login, av, sso=False):
        if not login:
            return
        if not self.hasKey(login):
            if not sso:
                # createIdentity expects a LoginInfo object, not a string!
                # However, _postLogin is never called for a non-existant identity unless SSO has been used.
                raise MaKaCError('postLogin called for new non-SSO identity')
            self.add(self.createIdentitySSO(login, av))
        elif not av.getIdentityById(login, self.getId()):
            av.addIdentity(self.getById(login))


class PIdentity(Persistent):

    def __init__(self, login, user):
        self.setLogin( login )
        self.setUser( user )

    def getId(self):
        return self.getLogin()

    def setUser(self, newUser):
        self.user = newUser
        newUser.addIdentity( self )

    def getUser(self):
        return self.user

    def setLogin(self, newLogin):
        self.login = newLogin.strip()

    def getLogin(self):
        return self.login

    def match(self, id):
        return self.getLogin() == id.getLogin()

    def authenticate(self, id):
        return None

class SSOHandler:

    def retrieveAvatar(self, rh):
        """
        Login using Shibbolet.
        """

        from MaKaC.user import AvatarHolder, Avatar
        config = Config.getInstance().getAuthenticatorConfigById(self.id).get("SSOMapping", {})

        if config.get('email', 'ADFS_EMAIL') in request.environ:
            email = request.environ[config.get("email", "ADFS_EMAIL")]
            login = request.environ.get(config.get("login", "ADFS_LOGIN"))
            personId = request.environ.get(config.get("personId", "ADFS_PERSONID"))
            phone = request.environ.get(config.get("phone", "ADFS_PHONENUMBER"), "")
            fax = request.environ.get(config.get("fax", "ADFS_FAXNUMBER"), "")
            lastname = request.environ.get(config.get("lastname", "ADFS_LASTNAME"), "")
            firstname = request.environ.get(config.get("firstname", "ADFS_FIRSTNAME"), "")
            institute = request.environ.get(config.get("institute", "ADFS_HOMEINSTITUTE"), "")
            if personId == '-1':
                personId = None
            ah = AvatarHolder()
            av = ah.match({"email": email}, exact=1, onlyActivated=False, searchInAuthenticators=False)
            if av:
                av = av[0]
                # don't allow disabled accounts
                if av.isDisabled():
                    return None
                elif not av.isActivated():
                    av.activateAccount()

                av.clearAuthenticatorPersonalData()
                av.setAuthenticatorPersonalData('phone', phone)
                av.setAuthenticatorPersonalData('fax', fax)
                av.setAuthenticatorPersonalData('surName', lastname)
                av.setAuthenticatorPersonalData('firstName', firstname)
                av.setAuthenticatorPersonalData('affiliation', institute)
                if personId != None and personId != av.getPersonId():
                    av.setPersonId(personId)
            else:
                avDict = {"email": email,
                          "name": firstname,
                          "surName": lastname,
                          "organisation": institute,
                          "telephone": phone,
                          "login": login}

                av = Avatar(avDict)
                ah.add(av)
                av.setPersonId(personId)
                av.activateAccount()

            self._postLogin(login, av, True)
            return av
        return None

    def getLogoutCallbackURL(self):
        return Config.getInstance().getAuthenticatorConfigById(self.id).get("LogoutCallbackURL")
