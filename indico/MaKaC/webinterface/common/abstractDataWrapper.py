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


class Author:
    
    def __init__(self,id,**data):
        self._id=id
        self.setValues(**data)

    def setValues(self, **data):
        self._title=data.get("title","")
        self._firstName=data.get("first_name","")
        self._familyName=data.get("family_name","")
        self._affiliation=data.get("affiliation","")
        self._email=data.get("email","")
        self._phone=data.get("phone","")
        self._speaker=data.get("isSpeaker",False)

    def mapAuthor(self,author):
        self._title=author.getTitle()
        self._firstName=author.getFirstName()
        self._familyName=author.getSurName()
        self._affiliation=author.getAffiliation()
        self._email=author.getEmail()
        self._phone=author.getTelephone()
        self._speaker=author.getAbstract().isSpeaker(author)

    def getTitle(self):
        return self._title

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getFirstName(self):
        return self._firstName

    def getFamilyName(self):
        return self._familyName

    def getAffiliation(self):
        return self._affiliation

    def getEmail(self):
        return self._email

    def getPhone(self):
        return self._phone

    def isSpeaker(self):
        return self._speaker

    def __str__(self):
        return "id:%s - nombre:%s"%(self._id, self._familyName)


class Abstract:
    
    def __init__(self, afm, **data):
        self._afm = afm
        self.setValues(**data)
    
    def setValues(self, **data):
        self._title=data.get("title", "")
        self._otherFields = {}
        for f in self._afm.getFields():
            id = f.getId()
            self._otherFields[id] = data.get(id,"").strip()
        self._contribTypeId=data.get("contribType", "")
        self._primAuthors=[]
        for i in range(len(data.get("auth_prim_id",[]))):
            id=data["auth_prim_id"][i]
            val={   "title":data["auth_prim_title"][i],
                    "first_name":data["auth_prim_first_name"][i],
                    "family_name":data["auth_prim_family_name"][i],
                    "affiliation":data["auth_prim_affiliation"][i],
                    "email":data["auth_prim_email"][i],
                    "phone":data["auth_prim_phone"][i],
                    "isSpeaker":id in data["auth_prim_speaker"] }
            id=len(self._primAuthors)
            self._primAuthors.append(Author(id,**val))
        self._coAuthors=[]
        for i in range(len(data.get("auth_co_id",[]))):
            id=data["auth_co_id"][i]
            val={ "title":data["auth_co_title"][i],
                    "first_name":data["auth_co_first_name"][i],
                    "family_name":data["auth_co_family_name"][i],
                    "affiliation":data["auth_co_affiliation"][i],
                    "email":data["auth_co_email"][i],
                    "phone":data["auth_co_phone"][i],
                    "isSpeaker":id in data["auth_co_speaker"] }
            id=len(self._coAuthors)
            self._coAuthors.append(Author(id,**val))

    def getOtherFieldValue( self, id ):
        return self._otherFields.get(id, "")

    def setOtherFieldValue( self, id, value ):
        self._otherFields[id] = value
    
    def mapAbstract(self, abstract):
        self._title=abstract.getTitle()
        self._otherFields = {}
        for key in abstract.getFields().keys():
            self._otherFields[key] = abstract.getField(key)
        self._contribTypeId=""
        if abstract.getContribType():
            self._contribTypeId=abstract.getContribType().getId()
        self._primAuthors=[]
        self._coAuthors=[]
        for author in abstract.getPrimaryAuthorList():
            a=Author(len(self._primAuthors))
            a.mapAuthor(author)
            self._primAuthors.append(a)
        for author in abstract.getCoAuthorList():
            a=Author(len(self._coAuthors))
            a.mapAuthor(author)
            self._coAuthors.append(a)

    def getTitle(self):
        return self._title

    def getContribTypeId(self):
        return self._contribTypeId

    def getPrimaryAuthorList(self):
        return self._primAuthors

    def getCoAuthorList(self):
        return self._coAuthors

    def hasErrors(self):
        return False

    def getErrors(self):
        return []

    def updateAbstract(self,abstract):
        abstract.setTitle(self.getTitle())
        for key in self._otherFields.keys():
            abstract.setField(key,self._otherFields[key])
        abstract.setContribType(abstract.getConference().getContribTypeById(self._contribTypeId))
        abstract.clearAuthors()
        for auth in self.getPrimaryAuthorList():
            abs_auth=abstract.newPrimaryAuthor()
            abs_auth.setTitle(auth.getTitle())
            abs_auth.setFirstName(auth.getFirstName())
            abs_auth.setSurName(auth.getFamilyName())
            abs_auth.setAffiliation(auth.getAffiliation())
            abs_auth.setEmail(auth.getEmail())
            abs_auth.setTelephone(auth.getPhone())
            if auth.isSpeaker():
                abstract.addSpeaker(abs_auth)
        for auth in self.getCoAuthorList():
            abs_auth=abstract.newCoAuthor()
            abs_auth.setTitle(auth.getTitle())
            abs_auth.setFirstName(auth.getFirstName())
            abs_auth.setSurName(auth.getFamilyName())
            abs_auth.setAffiliation(auth.getAffiliation())
            abs_auth.setEmail(auth.getEmail())
            abs_auth.setTelephone(auth.getPhone())
            if auth.isSpeaker():
                abstract.addSpeaker(abs_auth)

    def newPrimaryAuthor(self):
        self._primAuthors.append(Author(len(self._primAuthors)))

    def newCoAuthor(self):
        self._coAuthors.append(Author(len(self._coAuthors)))

    def _resetIds(self, l):
        i = 0
        for auth in l:
            auth.setId(i)
            i += 1
    
    def upPrimaryAuthors(self,id):
        i = 0
        pauth = None
        for auth in self._primAuthors:
            if str(auth.getId()) == str(id):
                pauth = auth
                break
            i += 1
        i -= 1
        if i>=0:
            self._primAuthors.remove(pauth)
            self._primAuthors.insert(i, pauth)
            self._resetIds(self._primAuthors)

    def downPrimaryAuthors(self,id):
        i = 0
        pauth = None
        for auth in self._primAuthors:
            if str(auth.getId()) == id:
                pauth = auth
                break
            i += 1
        i += 1
        if i<len(self._primAuthors):
            self._primAuthors.remove(pauth)
            self._primAuthors.insert(i, pauth)
            self._resetIds(self._primAuthors)

    def upCoAuthors(self,id):
        i = 0
        cauth = None
        for auth in self._coAuthors:
            if str(auth.getId()) == str(id):
                cauth = auth
                break
            i += 1
        i -= 1
        if i>=0:
            self._coAuthors.remove(cauth)
            self._coAuthors.insert(i, cauth)
            self._resetIds(self._coAuthors)

    def downCoAuthors(self,id):
        i = 0
        cauth = None
        for auth in self._coAuthors:
            if str(auth.getId()) == id:
                cauth = auth
                break
            i += 1
        i += 1
        if i<len(self._coAuthors):
            self._coAuthors.remove(cauth)
            self._coAuthors.insert(i, cauth)
            self._resetIds(self._coAuthors)
            
    def removePrimaryAuthors(self,idList):
        toRem=[]
        for auth in self._primAuthors:
            if str(auth.getId()) in idList:
                toRem.append(auth)
        for auth in toRem:
            self._primAuthors.remove(auth)
    
    def removeCoAuthors(self,idList):
        toRem=[]
        for auth in self._coAuthors:
            if str(auth.getId()) in idList:
                toRem.append(auth)
        for auth in toRem:
            self._coAuthors.remove(auth)



