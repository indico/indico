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

import bcrypt

from MaKaC.authentication.baseAuthentication import Authenthicator, PIdentity, SSOHandler
from MaKaC.i18n import _


class LocalAuthenticator(Authenthicator, SSOHandler):
    idxName = "localIdentities"
    id = "Local"
    name = "Indico"
    desciption = "Indico Login"

    def __init__(self):
        Authenthicator.__init__(self)

    def createIdentity(self, li, avatar):
        return LocalIdentity(li.getLogin(), li.getPassword(), avatar)

    def createIdentitySSO(self, login, avatar):
        return LocalIdentity(login, None, avatar)


class LocalIdentity(PIdentity):

    def __init__(self, login, password, user):
        PIdentity.__init__(self, login, user)
        self.setPassword(password)

    def setPassword(self, newPwd):
        self.algorithm = 'bcrypt'
        if newPwd is not None:
            self.password = bcrypt.hashpw(newPwd, bcrypt.gensalt())
        else:
            # This happens e.g. when SSO is used with Local identities.
            # The user can add the password later if he wants to anyway
            self.password = None

    def authenticate(self, id):
        if self.password is None:
            return None
        if self.getLogin() == id.getLogin() and self.password == bcrypt.hashpw(id.getPassword(), self.password):
            return self.user
        return None

    def getAuthenticatorTag(self):
        return LocalAuthenticator.getId()
