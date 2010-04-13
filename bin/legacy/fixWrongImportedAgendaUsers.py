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

import sys
sys.path.append("c:/development/indico/code/code")
import ldap

from MaKaC.common import DBMgr
from MaKaC import user



"""
Migration tool has imported users into Indico. Due to the format of agenda, the new users
in Indico don't have Surname nor affilation, and both fields are mandatory. This script is
aim to fix it, taking the info from NICE LDAP.
"""


def getNiceUserByEmail(email):

    ldapserver.protocol_version = ldap.VERSION3
    baseDN = "ou=people, o=cern, c=ch"
    searchScope = ldap.SCOPE_ONELEVEL
    retrieveAttributes = None
    searchFilter="mail=%s"%email
    ldap_result_id = ldapserver.search(baseDN, searchScope, searchFilter, retrieveAttributes)
    result_type, result_data = ldapserver.result(ldap_result_id, 0)
    if (result_data == []):
        return {}
    else:
        #proccess the entry
        dict = {}
        for k in result_data[0][1].keys():
            dict[k] = result_data[0][1][k][0]
        return dict
    return {}




DBMgr.getInstance().startRequest()
ldapserver = ldap.open("ldap.cern.ch:389")
error = False

ah=user.AvatarHolder()
notmodified=[]
modified=[]
notconfirmedNice=[]
withoutEmail=[]
for av in ah.getList():
    if av.getEmail().strip() == "":
        withoutEmail.append(av.getId())
    else:
        niceUserData=getNiceUserByEmail(av.getEmail())
        if av.getSurName().strip() == "" or \
            av.getFirstName().strip() == ""  or \
            av.getOrganisation().strip() == "":
            if niceUserData != {}:
                try:
                    if niceUserData['givenname']:
                        pass
                    if niceUserData['sn']:
                        pass
                    if niceUserData['homeinstitute']:
                        pass
                    modified.append(av.getId())
                    av.setName(niceUserData['givenname'])
                    av.setSurName(niceUserData['sn'])
                    if niceUserData['homeinstitute'].lower() != "unknown" or av.getOrganisation().strip()=="":
                        av.setOrganisation(niceUserData['homeinstitute'])
                except Exception, e:
                    print "error:%s,email:%s"%(e, av.getEmail())
            else:
                notmodified.append(av.getId())
        elif av.isNotConfirmed() and niceUserData != {}:
            if len(av.getIdentityList()) == 1 and av.getIdentityList()[0].getAuthenticatorTag() == "Nice":
                av.activateAccount()
                notconfirmedNice.append(av.getId())
    try:
        DBMgr.getInstance().commit()
        DBMgr.getInstance().sync()
    except Exception, e:
        print "error:%s"%e
        print ""
        print ""
        print "Without email (%s): %s"%(len(withoutEmail), withoutEmail)
        print "NICE to confirm (%s): %s"%(len(notconfirmedNice), notconfirmedNice)
        print "No data - Will be modified (%s): %s"%(len(modified), modified)
        print "No data - Will NOT be modified (%s): %s"%(len(notmodified), notmodified)
print ""
#if not error:
#    DBMgr.getInstance().endRequest()
#    print "No error. The change are saved"
#else:
#    print "There were errors. The changes was not saved"
try:
    DBMgr.getInstance().endRequest()
except Exception, e:
    print "error:%s"%e
    print ""
    print ""
    print "Without email (%s): %s"%(len(withoutEmail), withoutEmail)
    print "NICE to confirm (%s): %s"%(len(notconfirmedNice), notconfirmedNice)
    print "No data - Will be modified (%s): %s"%(len(modified), modified)
    print "No data - Will NOT be modified (%s): %s"%(len(notmodified), notmodified)

print ""
print ""
print "Without email (%s): %s"%(len(withoutEmail), withoutEmail)
print "NICE to confirm (%s): %s"%(len(notconfirmedNice), notconfirmedNice)
print "No data - Will be modified (%s): %s"%(len(modified), modified)
print "No data - Will NOT be modified (%s): %s"%(len(notmodified), notmodified)
