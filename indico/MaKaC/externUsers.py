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


import httplib
import urllib
import base64
from copy import copy
from xml.dom.minidom import parseString
from MaKaC.common.Configuration import Config
from MaKaC.i18n import _
from MaKaC.errors import MaKaCError

class ExtUserHolder:
    def __init__(self):
        self.extUserList = {"Nice":NiceUser}

    def getById(self, id):
        if id in self.extUserList.keys():
            return self.extUserList[id]()
        return None


class NiceUser:

    def match(self, criteria, exact=0):
        #'organisation': 'CERN', 'surName': 'bourillot', 'name': 'david', 'email': 'david.bouirllot@cern.ch'
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
            #headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
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
                #raise MaKaCError("Sorry, due to a temporary unavailability of the NICE service, we are unable to authenticate you. Please try later or use your local Indico account if you have one.")
            response = conn.getresponse()
            #print response.status, response.reason
            data = response.read()
            #print data
            conn.close()
            doc = parseString(data)
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

    def getById(self, id):
        params = urllib.urlencode({'DisplayName': "%s"%id})
        #headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
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
        #print response.status, response.reason
        data = response.read()
        #print data
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
        #try:
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
        from MaKaC.authentication.NiceAuthentication import NiceIdentity, NiceAuthenticator
        av["identity"] = NiceIdentity
        av["login"] = login
        av["authenticator"] = NiceAuthenticator()
        #except :
        #    av = None
        return av

    def getByLoginOrUPN(self, id):
        params = urllib.urlencode({'UserName': "%s"%id})
        #headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        cred = base64.encodestring("%s:%s"%(Config.getInstance().getNiceLogin(), Config.getInstance().getNicePassword()))[:-1]
        headers = {}
        headers["Content-type"] = "application/x-www-form-urlencoded"
        headers["Accept"] = "text/plain"
        headers["Authorization"] = "Basic %s"%cred
        conn = httplib.HTTPSConnection("winservices-soap.web.cern.ch")
        try:
            conn.request("POST", "/winservices-soap/generic/Authentication.asmx/GetUserInfoFromLogin", params, headers)
        except Exception, e:
            raise MaKaCError( _("Sorry, due to a temporary unavailability of the NICE service, we are unable to authenticate you. Please try later or use your local Indico account if you have one."))
        response = conn.getresponse()
        #print response.status, response.reason
        data = response.read()
        #print data
        conn.close()

        doc = parseString(data)
        elem = doc.getElementsByTagName("userInfo")[0]

        av = {}

        ccidTag = elem.getElementsByTagName("ccid")[0].childNodes
        if ccidTag:
            ccid = ccidTag[0].nodeValue.encode("utf-8")
            if ccid == "0" or ccid == "":
                return None
        else:
            return None

        email = elem.getElementsByTagName("email")[0].childNodes[0].nodeValue.encode("utf-8")
        av["email"] = [email]

        av["name"]=""
        nameTag=elem.getElementsByTagName("firstname")[0].childNodes
        if len(nameTag) > 0:
            av["name"] = nameTag[0].nodeValue.encode("utf-8")

        av["surName"]=""
        surnameTag=elem.getElementsByTagName("lastname")[0].childNodes
        if len(surnameTag) > 0:
            av["surName"] = surnameTag[0].nodeValue.encode("utf-8")

        av["telephone"]=""
        nameTag=elem.getElementsByTagName("telephonenumber")[0].childNodes
        if len(nameTag) > 0:
            av["telephone"] = nameTag[0].nodeValue.encode("utf-8")

        av["organisation"] = []
        if doc.getElementsByTagName("company"):
            if doc.getElementsByTagName("company")[0].childNodes:
                av["organisation"] = [elem.getElementsByTagName("company")[0].childNodes[0].nodeValue.encode("utf-8")]

        if av["organisation"] == []:
            nameTag=elem.getElementsByTagName("shortaffiliation")[0].childNodes
            if len(nameTag) > 0:
                av["organisation"] = [nameTag[0].nodeValue.encode("utf-8")]

        login = ""
        if doc.getElementsByTagName("login"):
            if doc.getElementsByTagName("login")[0].childNodes:
                login = doc.getElementsByTagName("login")[0].childNodes[0].nodeValue.encode("utf-8")
        av["login"] = login
        return av