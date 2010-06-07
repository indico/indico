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

from persistent import Persistent

from MaKaC.common.general import *
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.errors import UserError
from MaKaC.i18n import _

class Authenthicator(ObjectHolder):

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

        identity = self.getById( li.getLogin() )
        return identity.authenticate( li )
        #try:
        #    identity = self.getById( li.getLogin() )
        #except KeyError, e:
        #    return None
        #return identity.authenticate( li )

    def getAvatarByLogin(self, login):
        """ Returns an Avatar object, WITHOUT checking the password!
            Will throw KeyError if not found.

            :param login: the person's login string
            :type login: str
        """
        return self.getById(login).getUser()

    def getIdx(self):
        return self._getIdx()

    def getId(self):
        return self.id
    getId = classmethod( getId )

    def getName(self):
        return self.name

    def getDescription(self):
        return self.description

    def getUserCreator(self):
        return self.UserCreator

    def autoLogin(self, rh):
        return None

    def autoLogout(self, rh):
        return None




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
