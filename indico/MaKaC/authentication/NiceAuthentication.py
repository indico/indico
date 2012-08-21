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

import httplib
import urllib
import base64
import os
from copy import copy
from flask import request
from xml.dom.minidom import parseString

from MaKaC.authentication.baseAuthentication import Authenthicator, PIdentity, SSOHandler
from MaKaC.errors import MaKaCError
from MaKaC.webinterface import urlHandlers
from MaKaC.user import Avatar, CERNGroup
from MaKaC.common import Configuration
from MaKaC.common.Configuration import Config
from MaKaC.common.logger import Logger
from MaKaC.i18n import _


class NiceAuthenticator(Authenthicator, SSOHandler):
    idxName = "NiceIdentities"
    id = 'Nice'
    name = 'CERN user database'
    description = "NICE Login"

    def __init__(self):
        Authenthicator.__init__(self)

    def canUserBeActivated(self):
        return True

    def createIdentity(self, li, avatar):
        if NiceChecker().check(li.getLogin(), li.getPassword()):
            return NiceIdentity( li.getLogin(), avatar )
        else:
            return None

    def createUser(self, li):
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
        userList = ah.match({"email":data["mail"]}, searchInAuthenticators=False)
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

    #################
    #   Searching   #
    #################

    def matchUser(self, criteria, exact=0):
        dict = {}
        criteria = copy(criteria)
        criteria['organisation'] = ""
        if not criteria.has_key("surName"):
            criteria['surName'] = ""
        if not criteria.has_key("name"):
            criteria['name'] = ""
        if not criteria.has_key("email"):
            criteria['email'] = ""
        if criteria['surName'] != "" or criteria['name'] != "":
            if exact == 0:
                criteria['displayName'] = "*%s*%s*" % (criteria['name'],criteria['surName'])
            else:
                criteria['displayName'] = "%s * %s" % (criteria['name'],criteria['surName'])
            criteria['surName'] = ""
            criteria['name'] = ""
        if criteria['email'] != "":
            if exact == 0:
                criteria['email'] = "*%s*" % criteria['email']
        for value in criteria.values():
            if not value:
                continue
            params = urllib.urlencode({'DisplayName': value})
            cred = base64.encodestring("%s:%s"%(Config.getInstance().getNiceLogin(), Config.getInstance().getNicePassword()))[:-1]
            headers = {}
            headers["Content-type"] = "application/x-www-form-urlencoded"
            headers["Accept"] = "text/plain"
            headers["Authorization"] = "Basic %s"%cred
            conn = httplib.HTTPSConnection("winservices-soap.web.cern.ch")
            try:
                conn.request("POST", "/winservices-soap/generic/Authentication.asmx/ListUsers", params, headers)
            except Exception, e:
                return {}
            response = conn.getresponse()
            data = response.read()
            conn.close()
            try:
                doc = parseString(data)
            except Exception:
                Logger.get('auth.nice').exception("Returned text:\n%s\n" % data)
                raise
            for elem in doc.getElementsByTagName("userInfo"):
                email = elem.getElementsByTagName("email")[0].childNodes[0].nodeValue.encode("utf-8").lower()
                try:
                    av = {}
                    av["email"] = [email]
                    av["name"]=""
                    nameTag=elem.getElementsByTagName("firstname")[0].childNodes
                    if len(nameTag) > 0:
                        av["name"] = nameTag[0].nodeValue.encode("utf-8")
                    av["surName"]=""
                    surnameTag=elem.getElementsByTagName("lastname")[0].childNodes
                    if len(surnameTag) > 0:
                        av["surName"] = surnameTag[0].nodeValue.encode("utf-8")
                    av["login"] = elem.getElementsByTagName("login")[0].childNodes[0].nodeValue.encode("utf-8")
                    av["organisation"] = []
                    if elem.getElementsByTagName("company"):
                        if elem.getElementsByTagName("company")[0].childNodes:
                            av["organisation"] = [elem.getElementsByTagName("company")[0].childNodes[0].nodeValue.encode("utf-8")]
                    av["id"] = "Nice:%s"%email
                    av["status"] = "NotCreated"
                    dict[email] = av
                except :
                    pass
        return dict

    def searchUserById(self, id):
        params = urllib.urlencode({'DisplayName': "%s"%id})
        cred = base64.encodestring("%s:%s"%(Config.getInstance().getNiceLogin(), Config.getInstance().getNicePassword()))[:-1]
        headers = {}
        headers["Content-type"] = "application/x-www-form-urlencoded"
        headers["Accept"] = "text/plain"
        headers["Authorization"] = "Basic %s"%cred
        conn = httplib.HTTPSConnection("winservices-soap.web.cern.ch")
        try:
            conn.request("POST", "/winservices-soap/generic/Authentication.asmx/ListUsers", params, headers)
        except Exception, e:
            raise MaKaCError( _("Sorry, due to a temporary unavailability of the NICE service, we are unable to authenticate you. Please try later or use your local Indico account if you have one."))
        response = conn.getresponse()
        data = response.read()
        conn.close()
        av = None
        doc = parseString(data)
        elems = doc.getElementsByTagName("userInfo")
        if len(elems) > 1:
            raise _("More than one user for the id %s")%id
        if len(elems) < 1:
            return None
        elem = elems[0]

        email = elem.getElementsByTagName("email")[0].childNodes[0].nodeValue.encode("utf-8")
        av = {}
        av["email"] = [email]
        av["name"]=""
        nameTag=elem.getElementsByTagName("firstname")[0].childNodes
        if len(nameTag) > 0:
            av["name"] = nameTag[0].nodeValue.encode("utf-8")
        av["surName"]=""
        surnameTag=elem.getElementsByTagName("lastname")[0].childNodes
        if len(surnameTag) > 0:
            av["surName"] = surnameTag[0].nodeValue.encode("utf-8")
        av["organisation"] = []
        if doc.getElementsByTagName("company"):
            if doc.getElementsByTagName("company")[0].childNodes:
                av["organisation"] = [elem.getElementsByTagName("company")[0].childNodes[0].nodeValue.encode("utf-8")]
        login = ""
        if doc.getElementsByTagName("login"):
            if doc.getElementsByTagName("login")[0].childNodes:
                login = doc.getElementsByTagName("login")[0].childNodes[0].nodeValue.encode("utf-8")
        av["id"] = id
        av["status"] = "NotCreated"
        av["identity"] = NiceIdentity
        av["login"] = login
        av["authenticator"] = NiceAuthenticator()
        return av

    def _findGroups(self, criteria):
        params = urllib.urlencode({'pattern': criteria})
        cred = base64.encodestring("%s:%s"%(Config.getInstance().getNiceLogin(), Config.getInstance().getNicePassword()))[:-1]
        headers = {}
        headers["Content-type"] = "application/x-www-form-urlencoded"
        headers["Accept"] = "text/plain"
        headers["Authorization"] = "Basic %s"%cred
        try:
            conn = httplib.HTTPSConnection("winservices-soap.web.cern.ch")
            conn.request("POST", "/winservices-soap/generic/Authentication.asmx/SearchGroups", params, headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
        except Exception:
            raise MaKaCError( _("Sorry, due to a temporary unavailability of the NICE service, we are unable to authenticate you. Please try later or use your local Indico account if you have one."))
        doc = parseString(data)
        groupList = []
        for elem in doc.getElementsByTagName("string"):
            name = elem.childNodes[0].nodeValue.encode("utf-8")
            gr = CERNGroup()
            gr.setId(name)
            gr.setName(name)
            gr.setDescription("Mapping of the Nice group %s<br><br>\n"
                              "Members list: https://websvc02.cern.ch/WinServices/Services/GroupManager/GroupManager.aspx" %
                              name)
            groupList.append(gr)
        return groupList

    def matchGroup(self, criteria, exact=0):
        if not exact:
            criteria = "*%s*" % criteria
        return self._findGroups(criteria)

    def matchGroupFirstLetter(self, letter):
        criteria = "%s*" % letter
        return self._findGroups(criteria)

    def getGroupMemberList(self, group):
        params = urllib.urlencode( { 'ListName': group } )
        cred = base64.encodestring("%s:%s"%(Config.getInstance().getNiceLogin(), Config.getInstance().getNicePassword()))[:-1]
        headers = {}
        headers["Content-type"] = "application/x-www-form-urlencoded"
        headers["Accept"] = "text/plain"
        headers["Authorization"] = "Basic %s"%cred
        conn = httplib.HTTPSConnection( "winservices-soap.web.cern.ch" )
        try:
            conn.request( "POST", "/winservices-soap/generic/Authentication.asmx/GetListMembers", params, headers )
        except Exception, e:
            raise MaKaCError(  _("Sorry, due to a temporary unavailability of the NICE service, we are unable to authenticate you. Please try later or use your local Indico account if you have one."))
        response = conn.getresponse()
        #print response.status, response.reason
        data = response.read()
        #print data
        conn.close()

        try:
            doc = parseString( data )
        except:
            if "Logon failure" in data:
                return False
            raise MaKaCError( _("Nice authentication problem: %s")% data )

        elements = doc.getElementsByTagName( "string" )
        emailList = []
        for element in elements:
            emailList.append( element.childNodes[0].nodeValue.encode( "utf-8" ) )
        return emailList

    def isUserInGroup(self, user, group):
        params = urllib.urlencode({'UserName': user, 'GroupName': group})
        #headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        cred = base64.encodestring("%s:%s"%(Config.getInstance().getNiceLogin(), Config.getInstance().getNicePassword()))[:-1]
        headers = {}
        headers["Content-type"] = "application/x-www-form-urlencoded"
        headers["Accept"] = "text/plain"
        headers["Authorization"] = "Basic %s"%cred
        conn = httplib.HTTPSConnection("winservices-soap.web.cern.ch")
        try:
            conn.request("POST", "/winservices-soap/generic/Authentication.asmx/UserIsMemberOfGroup", params, headers)
        except Exception, e:
            raise MaKaCError( _("Sorry, due to a temporary unavailability of the NICE service, we are unable to authenticate you. Please try later or use your local Indico account if you have one."))
        try:
            response = conn.getresponse()
        except Exception, e:
            Logger.get("NICE").info("Error getting response from winservices: %s\nusername: %s\ngroupname: %s"%(e, id, group))
            raise
        data = response.read()
        conn.close()
        try:
            doc = parseString(data)
        except:
            if "Logon failure" in data:
                return False
            raise MaKaCError( _("Nice authentication problem: %s")%data)
        if doc.getElementsByTagName("boolean"):
            if doc.getElementsByTagName("boolean")[0].childNodes[0].nodeValue.encode("utf-8") == "true":
                return True
        return False

    #################
    # End Searching #
    #################

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

    def check(self, userName, Password):
        #Use the nue nice interface to retrieve the user data
        params = urllib.urlencode({'Username': userName, 'Password': Password})
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
        data = response.read()
        conn.close()

        if "<auth>" in data:
            auth = self.nodeText( data, "auth" )
            if auth != "3":
                return None
        else:
            return None

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
        return ret

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
