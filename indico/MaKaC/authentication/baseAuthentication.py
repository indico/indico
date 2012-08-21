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

from persistent import Persistent

from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.errors import UserError
from MaKaC.i18n import _
from MaKaC.common.Configuration import Config


class Authenthicator(ObjectHolder):

    def __init__(self):
        ObjectHolder.__init__(self)

    def add( self, newId ):
        if self.hasKey( newId.getId() ):
            raise UserError( _("identity already exists"))
        id = newId.getId()
        tree = self._getIdx()
        if tree.has_key(id):
            raise UserError
        tree[ id ] = newId
        return id

    def getAvatar( self, li ):
        """ Returns an Avatar object, checking that the password is right.

            :param li: a LoginInfo object with the person's login string and password
            :type li: MaKaC.user.LoginInfo
        """

        if self.hasKey(li.getLogin()):
            identity = self.getById( li.getLogin() )
            return identity.authenticate( li )
        return None

    def getAvatarByLogin(self, login):
        """ Returns an Avatar object, WITHOUT checking the password!
            Will throw KeyError if not found.

            :param login: the person's login string
            :type login: str
        """
        if self.hasKey(login):
            return self.getById(login).getUser()
        return None

    def getIdx(self):
        return self._getIdx()

    def getId(self):
        return self.id
    getId = classmethod( getId )

    def getName(self):
        return Config.getInstance().getAuthenticatorConfigById(self.getId()).get("name", self.name)

    def getDescription(self):
        return self.description

    def isSSOLoginActive(self):
        return Config.getInstance().getAuthenticatorConfigById(self.getId()).get("SSOActive", False)

    def canUserBeActivated(self):
        return False

    def SSOLogin(self, rh):
        return None

    def getLogoutCallbackURL(self, rh):
        return None

    def createIdentity(self, li, avatar):
        return None

    def createUser(self, li):
        return None

    def matchUser(self, criteria, exact=0):
        return None

    def matchUserFirstLetter(self, index, letter):
        return None

    def searchUserById(self, id):
        return None

    def matchGroup(self, criteria, exact=0):
        return None

    def matchGroupFirstLetter(self, letter):
        return None

    def getGroupMemberList(self, group):
        return None

    def isUserInGroup(self, user, group):
        return False


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
        return self.getLogin == id.getLogin()

    def authenticate(self, id):
        return None

class SSOHandler:

    def retrieveAvatar(self, rh):
        """
        Login using Shibbolet.
        """

        from MaKaC.user import AvatarHolder, Avatar
        config = Config.getInstance().getAuthenticatorConfigById(self.id).get("SSOMapping", {})

        req = rh._req
        req.add_common_vars()
        if  req.subprocess_env.has_key(config.get("email", "ADFS_EMAIL")):
            email = req.subprocess_env[config.get("email", "ADFS_EMAIL")]
            login = req.subprocess_env[config.get("personId", "ADFS_LOGIN")]
            personId = req.subprocess_env[config.get("personId", "ADFS_PERSONID")]
            phone = req.subprocess_env.get(config.get("phone", "ADFS_PHONENUMBER"),"")
            fax = req.subprocess_env.get(config.get("fax", "ADFS_FAXNUMBER"),"")
            lastname = req.subprocess_env.get(config.get("lastname", "ADFS_LASTNAME"),"")
            firstname = req.subprocess_env.get(config.get("firstname", "ADFS_FIRSTNAME"),"")
            institute = req.subprocess_env.get(config.get("institute", "ADFS_HOMEINSTITUTE"),"")
            if personId == '-1':
                personId = None
            ah = AvatarHolder()
            av = ah.match({"email":email},exact=1, onlyActivated=False, forceWithoutExtAuth=True)
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
                if phone != '' and phone != av.getPhone() and av.isFieldSynced('phone'):
                    av.setTelephone(phone)
                if fax != '' and fax != av.getFax() and av.isFieldSynced('fax'):
                    av.setFax(fax)
                if lastname != '' and lastname != av.getFamilyName() and av.isFieldSynced('surName'):
                    av.setSurName(lastname, reindex=True)
                if firstname != '' and firstname != av.getFirstName() and av.isFieldSynced('firstName'):
                    av.setName(firstname, reindex=True)
                if institute != '' and institute != av.getAffiliation() and av.isFieldSynced('affiliation'):
                    av.setAffiliation(institute, reindex=True)
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

            self._postLogin(login, av)
            return av
        return None

    def getLogoutCallbackURL(self, rh):
        return Config.getInstance().getAuthenticatorConfigById(self.id).get("LogoutCallbackURL", "https://login.cern.ch/adfs/ls/?wa=wsignout1.0")

    def _postLogin(self, login, av):
        if login != "" and not self.hasKey(login):
            ni = self.createIdentity(av, login)
            self.add(ni)
        if login != "" and self.hasKey(login) and not av.getIdentityById(login, self.getId()):
            av.addIdentity(self.getById(login))
