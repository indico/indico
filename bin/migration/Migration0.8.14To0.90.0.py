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

from indico.core.db import DBMgr
DBMgr.getInstance().startRequest()

from MaKaC.user import AvatarHolder

ah = AvatarHolder()
#migrate dict to list
for av in ah.getValuesToList():
    if not isinstance(av.identities, list):
        av.identities = av.identities.values()

from MaKaC.authentication.NiceAuthentication import NiceAuthenticator, NiceIdentity
na = NiceAuthenticator()
from MaKaC.authentication.LocalAuthentication import LocalAuthenticator
la = LocalAuthenticator()


#sync authenticators identities to avatars identity list
for id in la.getValuesToList():
    u = id.getUser()
    if not id in u.getIdentityList():
        try:
            u.addIdentity(id)
        except:
            print u.getId()

for id in na.getValuesToList():
    u = id.getUser()
    if not id in u.getIdentityList():
        try:
            u.addIdentity(id)
        except:
            print u.getId()

DBMgr.getInstance().endRequest()
