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

from MaKaC.authentication.baseAuthentication import Authenthicator, PIdentity
from MaKaC.errors import MaKaCError
from MaKaC.webinterface import urlHandlers
from MaKaC.user import Avatar
from MaKaC.common import Configuration
from MaKaC.common.Configuration import Config
from MaKaC.common.logger import Logger
from MaKaC.i18n import _


class NiceAuthenticator(Authenthicator):
    idxName = "NiceIdentities"
    id = 'Nice'
    name = 'CERN user database'
    description = "NICE Login"

    def __init__(self):
        Authenthicator.__init__(self)

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

    def autoLogin(self, rh):
        """
        Login using Shibbolet.
        """
        if 'ADFS_EMAIL' in request.environ:
            email = request.environ['ADFS_EMAIL']
            login = request.environ['ADFS_LOGIN']
            personId = request.environ['ADFS_PERSONID']
            phone = request.environ.get('ADFS_PHONENUMBER', "")
            fax = request.environ.get('ADFS_FAXNUMBER', "")
            lastname = request.environ.get('ADFS_LASTNAME', "")
            firstname = request.environ.get('ADFS_FIRSTNAME', "")
            institute = request.environ.get('ADFS_HOMEINSTITUTE', "")
            if personId == '-1':
                personId = None
            from MaKaC.user import AvatarHolder
            ah = AvatarHolder()
            av = ah.match({"email":email},exact=1, onlyActivated=False, searchInAuthenticators=False)
            if av:
                av = av[0]
                # don't allow disabled accounts
                if av.isDisabled():
                    return None
#                # TODO: is this checking necessary?
#                if av.getStatus() == 'NotCreated':
#                    #checking if comming from Nice
#                    if av.getId()[:len(self.id)] == self.id:
#                        av.setId("")
#                        ah.add(av) #XXXXX
#                        av.activateAccount()
#                    else:
#                        return None
                # if not activated
                elif not av.isActivated():
                    av.activateAccount()

                av.clearAuthenticatorPersonalData()
                av.setAuthenticatorPersonalData('phone', phone)
                av.setAuthenticatorPersonalData('fax', fax)
                av.setAuthenticatorPersonalData('surName', lastname)
                av.setAuthenticatorPersonalData('firstName', firstname)
                av.setAuthenticatorPersonalData('affiliation', institute)
                if phone != '' and phone != av.getPhone() and av.isFieldSynced('phone'):
                    av.setTelephone(phone)
                if fax != '' and fax != av.getFax() and av.isFieldSynced('fax'):
                    av.setFax(fax)
                if lastname != '' and lastname != av.getFamilyName() and av.isFieldSynced('surName'):
                    av.setSurName(lastname, reindex=True)
                if firstname != '' and firstname != av.getFirstName() and av.isFieldSynced('firstName'):
                    av.setName(firstname, reindex=True)
                if institute != '' and institute != av.getAffiliation() and av.isFieldSynced('affiliation'):
                    av.setAffiliation(institute, reindex=True)
                if personId != None and personId != av.getPersonId():
                    av.setPersonId(personId)
            else:
                avDict = {"email": email,
                          "name": firstname,
                          "surName": lastname,
                          "organisation": institute,
                          "telephone": phone,
                          "login": login}

                av = Avatar(avDict)
                ah.add(av)
                av.setPersonId(personId)
                av.activateAccount()

            if login != "" and not self.hasKey(login):
                ni=NiceIdentity(login, av)
                self.add(ni)
            if login != "" and self.hasKey(login) and not av.getIdentityById(login, self.getId()):
                av.addIdentity(self.getById(login))
            return av

        return None

    def autoLogout(self, rh):
        return "https://login.cern.ch/adfs/ls/?wa=wsignout1.0"


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
