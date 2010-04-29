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

class TplVar:
    _name=""
    _description=""
    
    def getName(cls):
        return cls._name
    getName=classmethod(getName)
    
    def getDescription(cls):
        return cls._description
    getDescription=classmethod(getDescription)
    
    def getLabel(cls):
        return "%%(%s)s"%cls.getName()
    getLabel=classmethod(getLabel)

    def getValue(cls,abstract):
        return ""
    getValue=classmethod(getValue)

class Notification:
    
    def __init__(self,subject="",body="",toList=[],fromAddr="",ccList=[]):
        self.setSubject(subject)
        self.setBody(body)
        self.setToList(toList)
        self.setFromAddr(fromAddr)
        self.setCCList(ccList)

    def setSubject(self,newSubject):
        self._subject=newSubject.strip()

    def getSubject(self):
        return self._subject

    def setBody(self,newBody=""):
        self._body=newBody.strip()

    def getBody(self):
        return self._body

    def setToList(self,newList):
        self._toList=[]
        for to in newList:
            self._toList.append(to)

    def getToList(self):
        return self._toList

    def setCCList(self,newList):
        self._ccList=[]
        for cc in newList:
            self._ccList.append(cc)

    def getCCList(self):
        return self._ccList

    def setFromAddr(self,newAddr):
        self._fromAddr=newAddr.strip()

    def getFromAddr(self):
        return self._fromAddr
