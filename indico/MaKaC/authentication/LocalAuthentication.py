# -*- coding: utf-8 -*-
##
## $Id: LocalAuthentication.py,v 1.3 2008/04/24 16:58:47 jose Exp $
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
from MaKaC.authentication.baseAuthentication import Authenthicator, PIdentity
from MaKaC.i18n import _


class LocalAuthenticator(Authenthicator):
    idxName = "localIdentities"
    id = "Local"
    name = "Indico"
    desciption = "Indico Login"
    UserCreator = None

    def createIdentity(self, li, avatar):
        return LocalIdentity(li.getLogin(), li.getPassword(), avatar)








class LocalIdentity(PIdentity):

    def __init__(self, login, password, user):
        PIdentity.__init__( self, login, user )
        self.setPassword( password )

    def setPassword( self, newPwd ):
        self.password = newPwd

    def authenticate( self, id ):
        if self.getLogin() == id.getLogin() and \
            self.password == id.getPassword():
            return self.user
        return None

    def getAuthenticatorTag(self):
        return LocalAuthenticator.getId()

