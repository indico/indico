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


class TplVar:
    _name = ""
    _description = ""

    @classmethod
    def getName(cls):
        return cls._name

    @classmethod
    def getDescription(cls):
        return cls._description

    @classmethod
    def getLabel(cls):
        return "%%(%s)s" % cls.getName()

    @classmethod
    def getValue(cls, abstract):
        return ""


class Notification:

    def __init__(self, subject="", body="", toList=[],
                 fromAddr="", ccList=[], content_type="text/plain"):
        self.setSubject(subject)
        self.setBody(body)
        self.setToList(toList)
        self.setFromAddr(fromAddr)
        self.setCCList(ccList)
        self._contenttype = content_type

    def getContentType(self):
        return self._contenttype

    def setContentType(self, contentType):
        self._contenttype = contentType

    def setSubject(self, newSubject):
        self._subject = newSubject.strip()

    def getSubject(self):
        return self._subject

    def setBody(self, newBody=""):
        self._body = newBody.strip()

    def getBody(self):
        return self._body

    def setToList(self, newList):
        self._toList = []
        for to in newList:
            self._toList.append(to)

    def getToList(self):
        return self._toList

    def setCCList(self, newList):
        self._ccList = []
        for cc in newList:
            self._ccList.append(cc)

    def getCCList(self):
        return self._ccList

    def setFromAddr(self, newAddr):
        self._fromAddr = newAddr.strip()

    def getFromAddr(self):
        return self._fromAddr
