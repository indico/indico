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

from MaKaC.common import DBMgr
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