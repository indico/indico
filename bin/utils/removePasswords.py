import sys
from MaKaC.common.db import DBMgr
from MaKaC.user import AvatarHolder
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.authentication.LocalAuthentication import LocalIdentity

print('This script will remove all local identities from users.')
print('This will remove passwords from the database and prevent them from')
print('logging in locally (so you need e.g. NICE or LDAP authentication)')
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
