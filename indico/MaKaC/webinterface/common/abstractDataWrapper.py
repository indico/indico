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

from MaKaC.common.fossilize import fossilizes, Fossilizable
from MaKaC.fossils.abstracts import IAuthorFossil
from MaKaC.webinterface.general import normaliseListParam
from indico.core.config import Config
from MaKaC.review import AbstractFieldContent

BYTES_1MB = 1024 * 1024


class Author(Fossilizable):

    fossilizes(IAuthorFossil)

    def __init__(self, id, **data):
        self._id = id
        self.setValues(**data)

    def setValues(self, **data):
        self._title = data.get("title", "")
        self._firstName = data.get("first_name", "")
        self._familyName = data.get("family_name", "")
        self._affiliation = data.get("affiliation", "")
        self._email = data.get("email", "")
        self._phone = data.get("phone", "")
        self._speaker = data.get("isSpeaker", False)

    def mapAuthor(self, author):
        self._title = author.getTitle()
        self._firstName = author.getFirstName()
        self._familyName = author.getSurName()
        self._affiliation = author.getAffiliation()
        self._email = author.getEmail()
        self._phone = author.getTelephone()
        self._speaker = author.getAbstract().isSpeaker(author)

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
        return "id:%s - nombre:%s" % (self._id, self._familyName)


class AbstractData(object):

    def __init__(self, absMgr, params, headerSize, displayValues=False):
        self._absMgr = absMgr
        self._afm = absMgr.getAbstractFieldsMgr()
        if (headerSize):
            self._headerSize = float(headerSize) / BYTES_1MB
        self._displayValues = displayValues
        cparams = params.copy()
        self._mapFromParams(cparams)

    def _mapFromParams(self, params):
        self.title = params.get("title", "").strip()
        self._otherFields = {}
        for f in self._afm.getFields():
            fid = f.getId()
            value = params.get("f_%s" % fid, "").strip()
            self._otherFields[fid] = value
        self.type = params.get("type", None)
        self.tracks = normaliseListParam(params.get("tracks", []))

        if self._displayValues:
            # the call comes from modifying an existing abstract, we want to display the current content in the abstract form
            self._prAuthorsListParam = params.get("prAuthors", [])
            self._coAuthorsListParam = params.get("coAuthors", [])
            self._setExistingAuthors()
        else:
            # the call comes from submitting a new abstract or modifying an existing abstract
            from MaKaC.services.interface.rpc import json
            self._prAuthorsListParam = json.decode(params.get("prAuthors", "[]"))
            self._coAuthorsListParam = json.decode(params.get("coAuthors", "[]"))
            self._setNewAuthors()
        self.comments = params.get("comments", "")
        self.origin = params.get("origin", "display")
        self.files = normaliseListParam(params.get("file", []))
        self.existingFiles = normaliseListParam(params.get("existingFile", []))

    def setAbstractData(self, abstract):
        conf = abstract.getConference()
        cfaMgr = conf.getAbstractMgr()
        afm = cfaMgr.getAbstractFieldsMgr()
        abstract.setTitle(self.title)
        for f in afm.getFields():
            fieldId = f.getId()
            abstract.setField(fieldId, self.getFieldValue(fieldId))
        # add primary authors
        for authData in self.getPrimaryAuthorList():
            auth = abstract.newPrimaryAuthor(title=authData.getTitle(),
                                             firstName=authData.getFirstName(),
                                             surName=authData.getFamilyName(),
                                             email=authData.getEmail(),
                                             affiliation=authData.getAffiliation(),
                                             address="",
                                             telephone=authData.getPhone())
            if authData.isSpeaker():
                abstract.addSpeaker(auth)
        # add co-authors
        for authData in self.getCoAuthorList():
            auth = abstract.newCoAuthor(title=authData.getTitle(),
                                        firstName=authData.getFirstName(),
                                        surName=authData.getFamilyName(),
                                        email=authData.getEmail(),
                                        affiliation=authData.getAffiliation(),
                                        address="",
                                        telephone=authData.getPhone())
            if authData.isSpeaker():
                abstract.addSpeaker(auth)
        abstract.setContribType(self.type)
        tracks = []
        for trackId in self.tracks:
            tracks.append(conf.getTrackById(trackId))
        abstract.setTracks(tracks)
        abstract.setComments(self.comments)
        abstract.deleteFilesNotInList(self.existingFiles)
        abstract.saveFiles(self.files)

    def _setNewAuthors(self):
        self._prAuthors = []
        for author in self._prAuthorsListParam:
            isSpeaker = author.get("isSpeaker", False)
            values = {"title": author["title"],
                      "first_name": author["firstName"],
                      "family_name": author["familyName"],
                      "affiliation": author["affiliation"],
                      "email": author["email"],
                      "phone": author["phone"],
                      "isSpeaker": isSpeaker
                      }

            authId = len(self._prAuthors)
            self._prAuthors.append(Author(authId, **values))

        self._coAuthors = []
        for author in self._coAuthorsListParam:
            isSpeaker = author.get("isSpeaker", False)
            values = {"title": author["title"],
                      "first_name": author["firstName"],
                      "family_name": author["familyName"],
                      "affiliation": author["affiliation"],
                      "email": author["email"],
                      "phone": author["phone"],
                      "isSpeaker": isSpeaker
                      }

            authId = len(self._prAuthors) + len(self._coAuthors)
            self._coAuthors.append(Author(authId, **values))

    def _setExistingAuthors(self):
        self._prAuthors = []
        for author in self._prAuthorsListParam:
            values = {"title": author.getTitle(),
                      "first_name": author.getFirstName(),
                      "family_name": author.getFamilyName(),
                      "affiliation": author.getAffiliation(),
                      "email": author.getEmail(),
                      "phone": author.getTelephone(),
                      "isSpeaker": author.isSpeaker()
                      }

            authId = len(self._prAuthors)
            self._prAuthors.append(Author(authId, **values))

        self._coAuthors = []
        for author in self._coAuthorsListParam:
            values = {"title": author.getTitle(),
                      "first_name": author.getFirstName(),
                      "family_name": author.getFamilyName(),
                      "affiliation": author.getAffiliation(),
                      "email": author.getEmail(),
                      "phone": author.getTelephone(),
                      "isSpeaker": author.isSpeaker()
                      }
            authId = len(self._prAuthors) + len(self._coAuthors)
            self._coAuthors.append(Author(authId, **values))

    def getFieldNames(self):
        return ['f_%s' % id for id in self._otherFields.keys()]

    def getFieldValue(self, id):
        return self._otherFields.get(id, "")

    def setFieldValue(self, id, value):
        self._otherFields[id] = value

    def getPrimaryAuthorList(self):
        return self._prAuthors

    def getCoAuthorList(self):
        return self._coAuthors

    def check(self):
        errors = []
        if self.title.strip() == "":
            errors.append(_("Abstract title cannot be empty"))
        for f in self._afm.getFields():
            value = self._otherFields.get(f.getId(), "")
            errors += f.check(value)
        if not self.origin == "management":
            if not self._prAuthorsListParam:
                errors.append(_("No primary author has been specified. You must define at least one primary author"))
            if not self._checkSpeaker() and self._absMgr.showSelectAsSpeaker() and self._absMgr.isSelectSpeakerMandatory():
                errors.append(_("At least one presenter must be specified"))
        if not self.tracks and self._absMgr.areTracksMandatory():
            # check if there are tracks, otherwise the user cannot select at least one
            if len(self._absMgr.getConference().getTrackList()) != 0:
                errors.append(_("At least one track must be seleted"))
        if self._hasExceededTotalSize():
            errors.append(_("The maximum size allowed for the attachments (%sMB) has been exceeded.") % Config.getInstance().getMaxUploadFilesTotalSize())
        return errors

    def _checkSpeaker(self):
        for author in self._prAuthors:
            if author.isSpeaker():
                return True
        for author in self._coAuthors:
            if author.isSpeaker():
                return True
        return False

    def _hasExceededTotalSize(self):
        maxSize = float(Config.getInstance().getMaxUploadFilesTotalSize())
        return maxSize > 0 and self._headerSize > maxSize

    def toDict(self):
        d = {"title": self.title,
             "type": self.type,
             "tracksSelectedList": self.tracks,
             "prAuthors": self._prAuthors,
             "coAuthors": self._coAuthors,
             "comments": self.comments,
             "attachments": self.files}
        for f in self._afm.getFields():
            id = f.getId()
            d["f_"+id] = self._otherFields.get(id, "")
        return d


class AbstractParam:

    def __init__(self):
        self._abstract = None

    def _checkParams(self, params, conf, headerSize):
        if params.has_key("abstractId"):  # we are in modify
            self._abstract = self._target = conf.getAbstractMgr().getAbstractById(params["abstractId"])

        self._action = ""
        if "cancel" in params:
            self._action = "CANCEL"
            return

        typeId = params.get("type", "")
        display_values = False

        params["type"] = conf.getContribTypeById(typeId)

        if ("prAuthors" not in params or "coAuthors" not in params) and self._abstract:
            params.update({
                "prAuthors": self._abstract.getPrimaryAuthorList(),
                "coAuthors": self._abstract.getCoAuthorList(),
                "file": self._abstract.getAttachments().values()
            })
            display_values = True

        self._abstractData = AbstractData(conf.getAbstractMgr(), params, headerSize, displayValues=display_values)

        if "validate" in params:
            self._action = "VALIDATE"
