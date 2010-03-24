# -*- coding: utf-8 -*-
##
## $Id: NiceAuthentication.py,v 1.17 2009/02/05 15:31:44 jose Exp $
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

import httplib
import urllib
import base64
import os
from MaKaC.common.general import *
from MaKaC.authentication.baseAuthentication import Authenthicator, PIdentity
from MaKaC.errors import MaKaCError
from MaKaC.webinterface import urlHandlers
from MaKaC.externUsers import NiceUser
from MaKaC.user import Avatar
from MaKaC.common import Configuration
from MaKaC.common.Configuration import Config
from MaKaC.i18n import _


class NiceAuthenticator(Authenthicator):
    idxName = "NiceIdentities"
    id = 'Nice'
    name = 'NICE'
    description = "NICE Login"

    def __init__(self):
        Authenthicator.__init__(self)
        self.UserCreator = NiceUserCreator()

    def createIdentity(self, li, avatar):
        if NiceChecker().check(li.getLogin(), li.getPassword()):
            return NiceIdentity( li.getLogin(), avatar )
        else:
            return None

    def autoLogin(self, rh):
        """
        Login using Shibbolet.
        """
        req = rh._req
        req.add_common_vars()
        if  req.subprocess_env.has_key("ADFS_EMAIL"):
            email = req.subprocess_env["ADFS_EMAIL"]
            login = req.subprocess_env["ADFS_LOGIN"]
#            phone = req.subprocess_env.get("ADFS_PHONENUMBER","")
#            lastname = req.subprocess_env.get("ADFS_LASTNAME","")
#            firstname = req.subprocess_env.get("ADFS_FIRSTNAME","")
            from MaKaC.user import AvatarHolder
            ah = AvatarHolder()
            av = ah.match({"email":email},exact=1, forceWithoutExtAuth=True)
            if av:
                return av[0]
            else:
                avDict = NiceUser().getByLoginOrUPN(login)
                if avDict:
                    # In the case of connected accounts (serveral accounts are related just to one
                    # of them), even if the login/email is different, the master account can already
                    # exist:
                    av = ah.match({"email":avDict["email"][0]},exact=1, forceWithoutExtAuth=True)
                    if av:
                        av = av[0]
                        if av.getStatus() == 'NotCreated':
                            #checking if comming from Nice
                            if av.getId()[:len(self.id)] == self.id:
                                av.setId("")
                                ah.add(av)
                                av.activateAccount()
                            else:
                                return None
                        elif not av.isActivated():
                            av.activateAccount()
                    else:
                        av = Avatar(avDict)
                        ah.add(av)
                        av.activateAccount()
                    return av
        return None

    def autoLogout(self, rh):
        return "https://login.cern.ch/adfs/ls/?wa=wsignout1.0"



class NiceIdentity(PIdentity):

    def authenticate( self, id ):
        ret = NiceChecker().check(id.getLogin(), id.getPassword())
        if ret:
            if ret['ccid']:
                if self.getLogin() == id.getLogin():
                    return self.user
                else:
                    return None
        return None

    def getAuthenticatorTag(self):
        return NiceAuthenticator.getId()


class NiceChecker:

##    def check(self, userName, Password):
##        params = urllib.urlencode({'Username': userName, 'Password': Password})
##        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
##        conn = httplib.HTTPSConnection("winservices.web.cern.ch")
##        try:
##            conn.request("POST", "/WinServices/Authentication/CDS/default.asp", params, headers)
##        except Exception, e:
##            raise MaKaCError("Sorry, due to a temporary unavailability of the NICE service, we are unable to authenticate you. Please try later or use your local Indico account if you have one.")
##        response = conn.getresponse()
##        #print response.status, response.reason
##        data = response.read()
##        #print data
##        conn.close()
##        m = re.search('<CCID>\d+</CCID>', data)
##        if m:
##            data=m.group()
##            CCID = int(re.search('\d+',data).group())
##            return CCID
##        return None

##    def check(self, userName, Password):
##        try:
##            params = urllib.urlencode({'Username': userName, 'Password': Password})
##            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
##            conn = httplib.HTTPSConnection("winservices-soap.web.cern.ch")
##            try:
##                conn.request("POST", "/winservices-soap/CDS/Authentication.asmx/GetUserInfo", params, headers)
##            except Exception, e:
##                raise MaKaCError("Sorry, due to a temporary unavailability of the NICE service, we are unable to authenticate you. Please try later or use your local Indico account if you have one.")
##            response = conn.getresponse()
##            #print response.status, response.reason
##            data = response.read()
##            #print data
##            conn.close()
##
##            from xml.dom.minidom import parseString
##            doc = parseString(data)
##            auth = doc.getElementsByTagName("auth")[0].childNodes[0].nodeValue.encode("utf-8")
##            if auth != "3":
##                return None
##            return doc.getElementsByTagName("ccid")[0].childNodes[0].nodeValue.encode("utf-8"), doc.getElementsByTagName("email")[0].childNodes[0].nodeValue.encode("utf-8")
##        except:
##            self.log("----------------------------")
##            self.log("Username: %s"%userName)
##            try:
##                self.log(data)
##            except:
##                pass
##            self.log("----------------------------")
##            return None


    def check(self, userName, Password):
        #Use the nue nice interface to retrieve the user data
##        try:
            params = urllib.urlencode({'Username': userName, 'Password': Password})
            #headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            cred = base64.encodestring("%s:%s"%(Config.getInstance().getNiceLogin(), Config.getInstance().getNicePassword()))[:-1]
            headers = {}
            headers["Content-type"] = "application/x-www-form-urlencoded"
            headers["Accept"] = "text/plain"
            headers["Authorization"] = "Basic %s"%cred
            conn = httplib.HTTPSConnection("winservices-soap.web.cern.ch")
            try:
                conn.request("POST", "/winservices-soap/generic/Authentication.asmx/GetUserInfo", params, headers)
            except Exception, e:
                raise MaKaCError( _("Sorry, due to a temporary unavailability of the NICE service, we are unable to authenticate you. Please try later or use your local Indico account if you have one."))
            response = conn.getresponse()
            #print response.status, response.reason
            data = response.read()
            #print data
            conn.close()

            if "<auth>" in data:
                auth = self.nodeText( data, "auth" )
                if auth != "3":
                    return None
            else:
                return None

            #from xml.dom.minidom import parseString
            #doc = parseString(data)

            #if doc.getElementsByTagName("auth"):
            #    auth = doc.getElementsByTagName("auth")[0].childNodes[0].nodeValue.encode("utf-8")
            #    if auth != "3":
            #        return None
            #else:
            #    return None

            ret = {'building': '',
                'division': '',
                'group': '',
                'cn': '',
                'ccid': '',
                'l': '',
                'o': '',
                'pmailbox': '',
                'telephonenumber': '',
                'sn': '',
                'uid': '',
                'mail': '',
                'ou': '',
                'givenname': '',
                'section': '',
                'homeinstitute': ''}

            if "<department>" in data:
                ret['group'] = self.nodeText( data, "department" )
            if "<name>" in data:
                ret['givenname'] = self.nodeText( data, "name" )
            if "<firstname>" in data:
                ret['cn'] = self.nodeText( data, "firstname" )
            if "<lastname>" in data:
                ret['sn'] = self.nodeText( data, "lastname" )
            if "<ccid>" in data:
                ret['ccid'] = self.nodeText( data, "ccid" )
                if ret['ccid'] == -1:
                    if "<respccid>" in data:
                        ret['respccid'] = self.nodeText( data, "respccid" )
            if "<telephonenumber>" in data:
                ret['telephonenumber'] = self.nodeText( data, "telephonenumber" )
            if "<login>" in data:
                ret['uid'] = self.nodeText( data, "login" )
            if "<login>" in data:
                ret['uid'] = self.nodeText( data, "login" )
            if "<email>" in data:
                ret['mail'] = self.nodeText( data, "email" )
            if "<email>" in data:
                ret['mail'] = self.nodeText( data, "email" )
            if "<company>" in data:
                ret['homeinstitute'] = self.nodeText( data, "company" )

#            if doc.getElementsByTagName("department"):
#                if doc.getElementsByTagName("department")[0].childNodes:
#                    ret['group'] = doc.getElementsByTagName("department")[0].childNodes[0].nodeValue.encode("utf-8")
#            if doc.getElementsByTagName("name"):
#                if doc.getElementsByTagName("name")[0].childNodes:
#                    ret['cn'] = doc.getElementsByTagName("name")[0].childNodes[0].nodeValue.encode("utf-8")
#            if doc.getElementsByTagName("firstname"):
#                if doc.getElementsByTagName("firstname")[0].childNodes:
#                    ret['sn'] = doc.getElementsByTagName("firstname")[0].childNodes[0].nodeValue.encode("utf-8")
#            if doc.getElementsByTagName("lastname"):
#                if doc.getElementsByTagName("lastname")[0].childNodes:
#                    ret['givenname'] = doc.getElementsByTagName("lastname")[0].childNodes[0].nodeValue.encode("utf-8")
#
#            if doc.getElementsByTagName("ccid"):
#                if doc.getElementsByTagName("ccid")[0].childNodes:
#                    ret['ccid'] = doc.getElementsByTagName("ccid")[0].childNodes[0].nodeValue.encode("utf-8")
#                    if ret['ccid'] == "-1":
#                        if doc.getElementsByTagName("respccid"):
#                            ret['ccid'] = doc.getElementsByTagName("respccid")[0].childNodes[0].nodeValue.encode("utf-8")
#
#            if doc.getElementsByTagName("telephonenumber"):
#                if doc.getElementsByTagName("telephonenumber")[0].childNodes:
#                    ret['telephonenumber'] = doc.getElementsByTagName("telephonenumber")[0].childNodes[0].nodeValue.encode("utf-8")
#            if doc.getElementsByTagName("login"):
#                if doc.getElementsByTagName("login")[0].childNodes:
#                    ret['uid'] = doc.getElementsByTagName("login")[0].childNodes[0].nodeValue.encode("utf-8")
#            if doc.getElementsByTagName("email"):
#                if doc.getElementsByTagName("email")[0].childNodes:
#                    ret['mail'] = doc.getElementsByTagName("email")[0].childNodes[0].nodeValue.encode("utf-8")
#            if doc.getElementsByTagName("company"):
#                if doc.getElementsByTagName("company")[0].childNodes:
#                    ret['homeinstitute'] = doc.getElementsByTagName("company")[0].childNodes[0].nodeValue.encode("utf-8")

            return ret
##        except:
##            self.log("----------------------------")
##            self.log("Username: %s"%userName)
##            try:
##                self.log(data)
##            except:
##                pass
##            self.log("----------------------------")
##            return None
    def log(self, txt):
        f = file(os.path.join(Configuration.Config.getInstance().getTempDir(), "nice.log"), 'a')
        f.write(txt)
        f.write("\n")
        f.close()

    # Dirty hack due to core dump in Python XML libraries
    # when run within mod_python with Python 2.4.5
    def nodeText( self, document, elementName ):
        """
        Returns text between <elementName> and </elementName>.
        !ASSUMES THAT ELEMENT HAS NO ATTRIBUTES!
        Accepts:
        document - string
        elementName - string
        """
        startIx = document.index( "<" + elementName + ">" ) + len( elementName ) + 2
        endIx = document.index( "</" + elementName + ">" )
        return document[startIx:endIx]


class NiceUserCreator:

    def create(self, li):
        # first, check if authentication is OK
        data = NiceChecker().check(li.getLogin(), li.getPassword())
        if not data:
            return None

        if (data["ccid"] == '') and (data['email'] == ""):
            return None

        if not data:
            # cannot get user data
            return None
        # Search if user already exist, using email address
        import MaKaC.user as user
        ah = user.AvatarHolder()
        userList = ah.match({"email":data["mail"]}, forceWithoutExtAuth=True)
        if len(userList) == 0:
            # User doesn't exist, create it
            try:
                av = user.Avatar()
                av.setName(data.get('cn', "No name"))
                av.setSurName(data.get('sn', "No Surname"))
                av.setOrganisation(data.get('homeinstitute', "No institute"))
                av.setEmail(data['mail'])
                av.setTelephone(data.get('telephonenumber',""))
                ah.add(av)
            except KeyError, e:
                raise MaKaCError( _("NICE account does not contain the mandatory data to create \
                                  an Indico account. You can create an Indico \
                                  account manually in order to use your NICE login")%(urlHandlers.UHUserRegistration.getURL()))
        else:
            # user founded
            av = userList[0]
        #now create the nice identity for the user
        na = NiceAuthenticator()
        id = na.createIdentity( li, av)
        na.add(id)
        return av


##    def getLdap(self, searchFilter):
##        ## first you must open a connection to the server
##        try:
##            l = ldap.open("ldap.cern.ch:389")
##            ## searching doesn't require a bind in LDAP V3.  If you're using LDAP v2, set the next line appropriately
##            ## and do a bind as shown in the above example.
##            # you can also set this to ldap.VERSION2 if you're using a v2 directory
##            # you should  set the next option to ldap.VERSION2 if you're using a v2 directory
##            l.protocol_version = ldap.VERSION3
##        except ldap.LDAPError, e:
##            print e
##            # handle error however you like
##
##
##        ## The next lines will also need to be changed to support your search requirements and directory
##        baseDN = "ou=people, o=cern, c=ch"
##        searchScope = ldap.SCOPE_ONELEVEL
##        ## retrieve all attributes - again adjust to your needs - see documentation for more options
##        retrieveAttributes = None
##        #searchFilter = "ccid=%s"%ccid
##
##        try:
##            ldap_result_id = l.search(baseDN, searchScope, searchFilter, retrieveAttributes)
##            result_set = []
##            while 1:
##                result_type, result_data = l.result(ldap_result_id, 0)
##                if (result_data == []):
##                    break
##                else:
##                    ## here you don't have to append to a list
##                    ## you could do whatever you want with the individual entry
##                    ## The appending to list is just for illustration.
##                    if result_type == ldap.RES_SEARCH_ENTRY:
##                        result_set.append(result_data)
##            ret = {}
##            for k in result_set[0][0][1].keys():
##                ret[k] = result_set[0][0][1][k][0]
##            return ret
##            """
##            return a dictionary. The keys are:
##                'building': '',
##                'division': '',
##                'group': '',
##                'cn': 'first and last name',
##                'ccid': '',
##                'l': 'town',
##                'o': 'user status',
##                'pmailbox': '',
##                'telephonenumber': '',
##                'sn': 'last name',
##                'uid': '',
##                'mail': 'address email',
##                'ou': 'division group section',
##                'givenname': 'first name',
##                'section': '',
##                'homeinstitute': ''
##            """
##        except ldap.LDAPError, e:
##            print e
