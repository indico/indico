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

import sys
from indico.core.db import DBMgr
from MaKaC.user import AvatarHolder
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.authentication.LocalAuthentication import LocalIdentity

print('This script will remove all local identities from users.')
print('This will remove passwords from the database and prevent them from')
print('logging in locally (so you need e.g. LDAP authentication)')
print
if raw_input('Do you want to continue? [yes|NO]: ').lower() != 'yes':
    print 'Cancelled.'
    sys.exit(0)

i = 0

dbi = DBMgr.getInstance()
dbi.startRequest()

ah = AvatarHolder()
am = AuthenticatorMgr()
for aid, avatar in ah._getIdx().iteritems():
    for identity in avatar.getIdentityList():
        if isinstance(identity, LocalIdentity):
            print('Removing LocalIdentity(%s, %s) from %s' %
                (identity.getLogin(), len(identity.password) * '*',
                    avatar.getFullName()))
            am.removeIdentity(identity)
            avatar.removeIdentity(identity)
    if i % 100 == 99:
        dbi.commit()
    i += 1
DBMgr.getInstance().endRequest()
