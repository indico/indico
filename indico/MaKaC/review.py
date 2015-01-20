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

from copy import copy
from pytz import timezone
from indico.util.string import safe_upper, safe_slice
from indico.util.i18n import i18nformat
import ZODB
from persistent import Persistent
from persistent.list import PersistentList
from BTrees.OOBTree import OOBTree, intersection, union
from BTrees.IOBTree import IOBTree
import BTrees.OIBTree as OIBTree
from datetime import datetime, timedelta
import MaKaC
from MaKaC.common.Counter import Counter
from MaKaC.errors import MaKaCError, NoReportError
from MaKaC.accessControl import AdminList
from MaKaC.trashCan import TrashCanManager
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.i18n import _
from indico.core.config import Config
from MaKaC.common.fossilize import fossilizes, Fossilizable
from MaKaC.fossils.abstracts import IAbstractFieldFossil
from MaKaC.fossils.abstracts import IAbstractTextFieldFossil
from MaKaC.fossils.abstracts import IAbstractSelectionFieldFossil
from MaKaC.fossils.abstracts import ISelectionFieldOptionFossil
from indico.util.i18n import N_
from indico.util.text import wordsCounter

import tempfile


class AbstractSorter:
    pass


class AbstractFilter:
    pass


class _AbstractParticipationIndex(Persistent):
    """This class allows to index abstract participations (submitters)
        for a single CFA process; this means that clients will be able to
        efficiently perform queries of the type "give me all the abstracts
        in which a certain registered user is implied".
       For being able to perform this indexing, it is supposed that the Avatar
        identifier is unique among other avatars and that it cannot change.
       This index must be maintained by clients (i.e. the CFAMgr) as it doesn't
        keep track of the changes on Participantons.
       The key of the index is the Avatar and the values the different
        Participations that user has within the current CFA process. For
        performance reasons, the Avatar id will be used as index key (using the
        whole Avatar object would make the index bigger and as the Avatar id
        cannot change it's enough); the clients would have to keep the
        integrity of the index.
    """

    def __init__(self):
        self._idx = OOBTree()

    def index(self, participation):
        """Add a new participation to the index
        """
        #if the Participation is not linked to an Avatar there's no point to
        #   index it
        a = participation.getAvatar()
        if not a:
            return
        #ToDo: if the Participation corresponds to an abstract which doesn't
        #   correspond to the current CFAMgr, then an error must be raised

        if not self._idx.has_key(a.getId()):
            self._idx[a.getId()] = PersistentList()
        #if the participation is already in the index, no need for adding it
        if participation in self._idx[a.getId()]:
            return
        self._idx[a.getId()].append(participation)

    def unindex(self, participation):
        """Remove an existing participation from the index
        """
        #if the Participation is not linked to an Avatar there's no point to
        #   unindex it
        a = participation.getAvatar()

        if not a:
            return
        #if the Avatar associated to the participation isn't in the index do
        #   nothing
        if not self._idx.has_key(a.getId()):
            return
        #if the given participation is indexed remove it, otherwise do nothing
        if participation in self._idx[a.getId()]:
            self._idx[a.getId()].remove(participation)

    def getParticipationList(self, av):
        try:
            return self._idx[av.getId()]
        except KeyError, e:
            return []


class AbstractParticipation(Persistent):

    def __init__(self, abstract, **data):
        self._abstract = abstract
        self._firstName = ""
        self._surName = ""
        self._email = ""
        self._affilliation = ""
        self._address = ""
        self._telephone = ""
        self._fax = ""
        self._title = ""
        self.setData(**data)

    def setFromAvatar(self, av):
        data = {"title": av.getTitle(),
                "firstName": av.getName(),
                "surName": av.getSurName(),
                "email": av.getEmail(),
                "affiliation": av.getOrganisation(),
                "address": av.getAddress(),
                "telephone": av.getTelephone(),
                "fax": av.getFax()}
        self.setData(**data)

    def setFromAbstractParticipation(self, part):
        data = {"title": part.getTitle(),
                "firstName": part.getFirstName(),
                "surName": part.getSurName(),
                "email": part.getEmail(),
                "affiliation": part.getAffiliation(),
                "address": part.getAddress(),
                "telephone": part.getTelephone(),
                "fax": part.getFax()}
        self.setData(**data)

    def setData(self, **data):
        if "firstName" in data:
            self.setFirstName(data["firstName"])
        if "surName" in data:
            self.setSurName(data["surName"])
        if "email" in data:
            self.setEmail(data["email"])
        if "affiliation" in data:
            self.setAffiliation(data["affiliation"])
        if "address" in data:
            self.setAddress(data["address"])
        if "telephone" in data:
            self.setTelephone(data["telephone"])
        if "fax" in data:
            self.setFax(data["fax"])
        if "title" in data:
            self.setTitle(data["title"])
    setValues = setData

    def getData(self):
        data = {}
        data["firstName"] = self.getFirstName()
        data["surName"] = self.getSurName()
        data["email"] = self.getEmail()
        data["affiliation"] = self.getAffiliation()
        data["address"] = self.getAddress()
        data["telephone"] = self.getTelephone()
        data["fax"] = self.getFax()
        data["title"] = self.getTitle()

        return data
    getValues = getData

    def clone(self, abstract):
        ap = AbstractParticipation(abstract, self.getData())
        return ap

    def _notifyModification(self):
        self._abstract._notifyModification()

    def _unindex(self):
        abs = self.getAbstract()
        if abs is not None:
            mgr = abs.getOwner()
            if mgr is not None:
                mgr.unindexAuthor(self)

    def _index(self):
        abs = self.getAbstract()
        if abs is not None:
            mgr = abs.getOwner()
            if mgr is not None:
                mgr.indexAuthor(self)

    def setFirstName(self, name):
        tmp = name.strip()
        if tmp == self.getFirstName():
            return
        self._unindex()
        self._firstName = tmp
        self._index()
        self._notifyModification()

    def getFirstName(self):
        return self._firstName

    def getName(self):
        return self._firstName

    def setSurName(self, name):
        tmp = name.strip()
        if tmp == self.getSurName():
            return
        self._unindex()
        self._surName = tmp
        self._index()
        self._notifyModification()

    def getSurName(self):
        return self._surName

    def getFamilyName(self):
        return self._surName

    def setEmail(self, email):
        email = email.strip().lower()
        if email != self.getEmail():
            self._unindex()
            self._email = email
            self._index()
            self._notifyModification()

    def getEmail(self):
        return self._email

    def setAffiliation(self, af):
        self._affilliation = af.strip()
        self._notifyModification()

    setAffilliation = setAffiliation

    def getAffiliation(self):
        return self._affilliation

    def setAddress(self, address):
        self._address = address.strip()
        self._notifyModification()

    def getAddress(self):
        return self._address

    def setTelephone(self, telf):
        self._telephone = telf.strip()
        self._notifyModification()

    def getTelephone(self):
        return self._telephone

    def setFax(self, fax):
        self._fax = fax.strip()
        self._notifyModification()

    def getFax(self):
        return self._fax

    def setTitle(self, title):
        self._title = title.strip()
        self._notifyModification()

    def getTitle(self):
        return self._title

    def getFullName(self):
        res = safe_upper(self.getSurName())
        tmp = []
        for name in self.getFirstName().lower().split(" "):
            if not name.strip():
                continue
            name = name.strip()
            tmp.append(safe_upper(safe_slice(name, 0, 1)) + safe_slice(name, 1))
        firstName = " ".join(tmp)
        if firstName:
            res = "%s, %s" % (res, firstName)
        if self.getTitle():
            res = "%s %s" % (self.getTitle(), res)
        return res

    def getStraightFullName(self):
        name = ""
        if self.getName():
            name = "%s " % self.getName()
        return "%s%s" % (name, self.getSurName())

    def getAbrName(self):
        res = self.getSurName()
        if self.getFirstName():
            if res:
                res = "%s, " % res
            res = "%s%s." % (res, safe_upper(safe_slice(self.getFirstName(), 0, 1)))
        return res

    def getAbstract(self):
        return self._abstract

    def setAbstract(self, abs):
        self._abstract = abs

    def delete(self):
        self._unindex()
        self._abstract = None
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)


class Author(AbstractParticipation):

    def __init__(self, abstract, **data):
        AbstractParticipation.__init__(self, abstract, **data)
        self._abstractId = ""

    def getId(self):
        return self._id

    def setId(self, newId):
        self._id = str(newId)

    def clone(self, abstract):
        auth = Author(abstract, self.getData())
        return auth

    def isSpeaker(self):
        return self._abstract.isSpeaker(self)


class Submitter(AbstractParticipation):

    def __init__(self, abstract, av):
        if av is None:
            raise MaKaCError(_("abstract submitter cannot be None"))
        AbstractParticipation.__init__(self, abstract)
        self._user = None
        self._setUser(av)
        self.setFromAvatar(av)

    def _setUser(self, av):
        if self.getUser() == av:
            return
        #if currently there's an association with a registered user, we notify
        #   the unidexation of the participation
        if self.getUser():
            self.getAbstract().getOwner().unregisterParticipation(self)
        self._user = av
        #if the participation is associated to any avatar, we make the
        #   association and index it
        if self.getUser():
            self.getAbstract().getOwner().registerParticipation(self)

    def clone(self, abstract):
        sub = Submitter(abstract, self.getAvatar())
        sub.setData(self.getData())
        return sub

    def getUser(self):
        return self._user

    def getAvatar(self):
        return self._user

    def representsUser(self, av):
        return self.getUser() == av


class _AuthIdx(Persistent):

    def __init__(self, mgr):
        self._mgr = mgr
        self._idx = OOBTree()

    def _getKey(self, auth):
        return "%s %s" % (auth.getSurName().lower(), auth.getFirstName().lower())

    def index(self, auth):
        if auth.getAbstract() is None:
            raise MaKaCError(_("cannot index an author of an abstract which is not included in a conference"))
        if auth.getAbstract().getOwner() != self._mgr:
            raise MaKaCError(_("cannot index an author of an abstract which does not belong to this conference"))
        key = self._getKey(auth)
        abstractId = str(auth.getAbstract().getId())
        if not self._idx.has_key(key):
            self._idx[key] = OIBTree.OIBTree()
        if not self._idx[key].has_key(abstractId):
            self._idx[key][abstractId] = 0
        self._idx[key][abstractId] += 1

    def unindex(self, auth):
        if auth.getAbstract() is None:
            raise MaKaCError(_("cannot unindex an author of an abstract which is not included in a conference"))
        if auth.getAbstract().getOwner() != self._mgr:
            raise MaKaCError(_("cannot unindex an author of an abstract which does not belong to this conference"))
        key = self._getKey(auth)
        if not self._idx.has_key(key):
            return
        abstractId = str(auth.getAbstract().getId())
        if abstractId not in self._idx[key]:
            return
        self._idx[key][abstractId] -= 1
        if self._idx[key][abstractId] <= 0:
            del self._idx[key][abstractId]
        if len(self._idx[key]) <= 0:
            del self._idx[key]

    def match(self, query):
        query = query.lower().strip()
        res = OIBTree.OISet()
        for k in self._idx.keys():
            if k.find(query) != -1:
                res = OIBTree.union(res, self._idx[k])
        return res


class _PrimAuthIdx(_AuthIdx):

    def __init__(self, mgr):
        _AuthIdx.__init__(self, mgr)
        for abs in self._mgr.getAbstractList():
            for auth in abs.getPrimaryAuthorList():
                self.index(auth)


class _AuthEmailIdx(_AuthIdx):

    def __init__(self, mgr):
        _AuthIdx.__init__(self, mgr)
        for abs in self._mgr.getAbstractList():
            for auth in abs.getPrimaryAuthorList():
                self.index(auth)
            for auth in abs.getCoAuthorList():
                self.index(auth)

    def _getKey(self, auth):
        return auth.getEmail().lower()


class AbstractField(Persistent, Fossilizable):
    fossilizes(IAbstractFieldFossil)

    fieldtypes = ["textarea", "input", "selection"]

    @classmethod
    def makefield(cls, params):
        fieldType = params["type"]
        if fieldType not in cls.fieldtypes:
            return AbstractTextAreaField(params)
        elif fieldType == "textarea":
            return AbstractTextAreaField(params)
        elif fieldType == "input":
            return AbstractInputField(params)
        elif fieldType == "selection":
            return AbstractSelectionField(params)

    def __init__(self, params):
        self._id = params["id"]
        self._caption = params.get("caption") if params.get("caption") else self._id
        self._isMandatory = params.get("isMandatory") if params.get("isMandatory") else False
        self._active = True

    def clone(self):
        """ To be implemented by subclasses """
        pass

    def _notifyModification(self):
        self._p_changed = 1

    def check(self, content):
        errors = []

        if self._active and self._isMandatory and content == "":
                errors.append(_("The field '%s' is mandatory") % self._caption)

        return errors

    def getType(self):
        return self._type

    def isMandatory(self):
        return self._isMandatory

    def setMandatory(self, isMandatory=False):
        self._isMandatory = isMandatory
        self._notifyModification()

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id
        self._notifyModification()

    def getCaption(self):
        return self._caption

    def setCaption(self, caption):
        self._caption = caption
        self._notifyModification()

    def isActive(self):
        return self._active

    def setActive(self, active):
        self._active = active
        self._notifyModification()

    def getValues(self):
        values = []
        values["id"] = self.getId()
        values["caption"] = self.getCaption()
        values["isMandatory"] = self.isMandatory()
        return values

    def setValues(self, params):
        self.setCaption(params.get("caption") if params.get("caption") else self._id)
        self.setMandatory(params.get("isMandatory") if params.get("isMandatory") else False)
        self._notifyModification()


class AbstractTextField(AbstractField):
    fossilizes(IAbstractTextFieldFossil)

    limitationtypes = ["chars", "words"]

    def __init__(self, params):
        AbstractField.__init__(self, params)
        self._maxLength = params.get("maxLength") if params.get("maxLength") else 0
        self._limitation = params.get("limitation") if params.get("limitation") in self.limitationtypes else "chars"

    def clone(self):
        return AbstractTextField(self.getValues())

    def check(self, content):
        errors = AbstractField.check(self, content)

        if self._maxLength != 0:
            if self._limitation == "words" and wordsCounter(str(content)) > self._maxLength:
                errors.append(_("The field '%s' cannot be more than %s words") % (self._caption, self._maxLength))
            elif self._limitation == "chars" and len(content) > self._maxLength:
                errors.append(_("The field '%s' cannot be more than %s characters") % (self._caption, self._maxLength))

        return errors

    def getLimitation(self):
        return self._limitation

    def getMaxLength(self):
        return self._maxLength

    def setLimitation(self, limitation="chars"):
        self._limitation = limitation if limitation in self.limitationtypes else "chars"
        self._notifyModification()

    def setMaxLength(self, maxLength=0):
        self._maxLength = maxLength
        self._notifyModification()

    def getValues(self):
        values = AbstractField.getValues(self)
        values["maxLength"] = self.getMaxLength()
        values["limitation"] = self.getLimitation()
        return values

    def setValues(self, params):
        AbstractField.setValues(self, params)
        self.setMaxLength(params.get("maxLength") if params.get("maxLength") else 0)
        self.setLimitation(params.get("limitation") if params.get("limitation") in self.limitationtypes else "chars")
        self._notifyModification()


class AbstractTextAreaField(AbstractTextField):
    _type = "textarea"
    pass


class AbstractInputField(AbstractTextField):
    _type = "input"
    pass


class AbstractSelectionField(AbstractField):
    fossilizes(IAbstractSelectionFieldFossil)
    _type = "selection"

    def __init__(self, params):
        AbstractField.__init__(self, params)
        self.__id_generator = Counter()
        self._options = []
        self._deleted_options = []
        for o in params.get("options") if params.get("options") else []:
            self._setOption(o)

    def _deleteOption(self, option):
        self._options.remove(option)
        self._deleted_options.append(option)

    def _updateDeletedOptions(self, options=[]):
        stored_options = set(self._options)
        updated_options = set(self.getOption(o["id"]) for o in options)

        for deleted_option in stored_options - updated_options:
            self._deleteOption(deleted_option)

    def _setOption(self, option, index=None):
        stored = self.getOption(option["id"])
        if stored:
            stored.value = option["value"]
            oldindex = self._options.index(stored)
            self._options.insert(index, self._options.pop(oldindex))
        elif option["value"] is not "":
            option["id"] = self.__id_generator.newCount()
            self._options.append(SelectionFieldOption(option["id"], option["value"]))

    def clone(self):
        return AbstractSelectionField(self.getValues())

    def check(self, content):
        errors = AbstractField.check(self, content)

        if self._active and self._isMandatory and content == "":
            errors.append(_("The field '%s' is mandatory") % self._caption)
        elif content != "":
            if next((op for op in self._options if op.id == content), None) is None:
                errors.append(_("The option with ID '%s' in the field %s") % (content, self._caption))

        return errors

    def getDeletedOption(self, id):
        return next((o for o in self._deleted_options if o.getId() == id), None)

    def getDeletedOptions(self, id):
        return self._deleted_options

    def getOption(self, id):
        return next((o for o in self._options if o.getId() == id), None)

    def getOptions(self):
        return self._options

    def setOptions(self, options=[]):
        self._updateDeletedOptions(options)
        for i, o in enumerate(options):
            self._setOption(o, i)
        self._notifyModification()

    def getValues(self):
        values = AbstractField.getValues(self)

        options = []
        for o in self._options:
            options.append(o.__dict__)
        values["options"] = options

        return values

    def setValues(self, params):
        AbstractField.setValues(self, params)
        self.setOptions(params.get("options"))
        self._notifyModification()


class SelectionFieldOption(Fossilizable):
    fossilizes(ISelectionFieldOptionFossil)

    def __init__(self, id, value):
        self.id = id
        self.value = value
        self.deleted = False

    def __eq__(self, other):
        if isinstance(other, SelectionFieldOption):
            return self.id == other.id
        return False

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return self.id

    def __str__(self):
        return self.value

    def getValue(self):
        return self.value

    def getId(self):
        return self.id

    def isDeleted(self):
        return self.deleted


class AbstractFieldContent(Persistent):

    def __init__(self, field, value):
        self.field = field
        self.value = value

    def __eq__(self, other):
        if isinstance(other, AbstractFieldContent) and self.field == other.field:
            return self.value == other.value
        elif not isinstance(other, AbstractFieldContent):
            return self.value == other
        return False

    def __len__(self):
        return len(self.value)

    def __ne__(self, other):
        if isinstance(other, AbstractFieldContent) and self.field == other.field:
            return self.value != other.value
        elif not isinstance(other, AbstractFieldContent):
            return self.value != other
        return True

    def __str__(self):
        if isinstance(self.field, AbstractSelectionField):
            return str(self.field.getOption(self.value))
        else:
            return str(self.value)


class AbstractFieldsMgr(Persistent):

    def __init__(self):
        self._fields = self._initFields()
        self.__fieldGenerator = Counter()

    def clone(self):
        afm = AbstractFieldsMgr()
        for f in self.getFields():
            afm._addField(f.clone())
        return afm

    def getFieldGenerator(self):
        try:
            if self.__fieldGenerator:
                pass
        except AttributeError, e:
            self.__fieldGenerator = Counter()
        return self.__fieldGenerator

    def _notifyModification(self):
        self._p_changed = 1

    def _initFields(self):
        d = []
        params = {"type": "textarea", "id": "content", "caption": N_("Content"), "isMandatory": True}
        d.append(AbstractField.makefield(params))
        params = {"type": "textarea", "id": "summary", "caption": N_("Summary")}
        d.append(AbstractField.makefield(params))
        return d

    def hasField(self, id):
        for f in self._fields:
            if f.getId() == id:
                return True
        return False

    def getFields(self):
        if not self.hasField("content"):
            params = {"type": "textarea", "id": "content", "caption": _("Content"), "isMandatory": True}
            ac = AbstractField.makefield(params)
            self._fields.insert(0, ac)
        return self._fields

    def getActiveFields(self):
        fl = []
        for f in self.getFields():
            if f.isActive():
                fl.append(f)
        return fl

    def hasActiveField(self, id):
        return self.hasField(id) and self.getFieldById(id).isActive()

    def hasAnyActiveField(self):
        for f in self._fields:
            if f.isActive():
                return True
        return False

    def enableField(self, id):
        if self.hasField(id):
            self.getFieldById(id).setActive(True)
            self._notifyModification()

    def disableField(self, id):
        if self.hasField(id):
            self.getFieldById(id).setActive(False)
            self._notifyModification()

    def getFieldKeys(self):
        keys = []
        for f in self._fields:
            keys.append(f.getId())
        return keys

    def getFieldById(self, id):
        for f in self._fields:
            if f.getId() == id:
                return f
        return None

    def _addField(self, field):
        self._fields.append(field)

    def setField(self, params):
        if self.hasField(params["id"]):
            self.getFieldById(params["id"]).setValues(params)
        else:
            params["id"] = str(self.getFieldGenerator().newCount())
            absf = AbstractField.makefield(params)
            self._fields.append(absf)
        self._notifyModification()
        return params["id"]

    def removeField(self, id):
        if self.hasField(id):
            self._fields.remove(self.getFieldById(id))
            self._notifyModification()

    def moveAbsFieldUp(self, id):
        if self.hasField(id):
            f = self.getFieldById(id)
            idx = self._fields.index(f)
            self._fields.remove(f)
            if idx == 0:
                self._fields.append(f)
            else:
                self._fields.insert(idx-1, f)
            self._notifyModification()

    def moveAbsFieldDown(self, id):
        if self.hasField(id):
            f = self.getFieldById(id)
            idx = self._fields.index(f)
            self._fields.remove(f)
            if idx == len(self._fields):
                self._fields.insert(0, f)
            else:
                self._fields.insert(idx+1, f)
            self._notifyModification()


class AbstractMgr(Persistent):

    def __init__(self, owner):
        self._owner = owner
        self._abstracts = OOBTree()
        self._participationIdx = _AbstractParticipationIndex()
        self.__abstractGenerator = Counter()
        self._activated = False
        self.setStartSubmissionDate(datetime.now())
        self.setEndSubmissionDate(datetime.now())
##        self._contribTypes = PersistentList()
        self.setAnnouncement("")
        self._notifTpls = IOBTree()
        self._notifTplsOrder = PersistentList()
        self.__notifTplsCounter = Counter()
        self._authorizedSubmitter = PersistentList()
        self._primAuthIdx = _PrimAuthIdx(self)
        self._authEmailIdx = _AuthEmailIdx(self)
        self._abstractFieldsMgr = AbstractFieldsMgr()
        self._submissionNotification = SubmissionNotification()
        self._multipleTracks = True
        self._tracksMandatory = False
        self._attachFiles = False
        self._showSelectAsSpeaker = True
        self._selectSpeakerMandatory = True
        self._showAttachedFilesContribList = False

    def getMultipleTracks(self):
        try:
            return self._multipleTracks
        except:
            self.setMultipleTracks(True)
            return self._multipleTracks

    def setMultipleTracks(self, multipleTracks=True):
        self._multipleTracks = multipleTracks

    def areTracksMandatory(self):
        try:
            return self._tracksMandatory
        except:
            self.setTracksMandatory(False)
            return self._tracksMandatory

    def canAttachFiles(self):
        try:
            return self._attachFiles
        except:
            self.setAllowAttachFiles(False)
            return self._attachFiles

    def setAllowAttachFiles(self, attachedFiles):
        self._attachFiles = attachedFiles

    def setTracksMandatory(self, tracksMandatory=False):
        self._tracksMandatory = tracksMandatory

    def showSelectAsSpeaker(self):
        try:
            return self._showSelectAsSpeaker
        except:
            self._showSelectAsSpeaker = True
            return self._showSelectAsSpeaker

    def setShowSelectAsSpeaker(self, showSelectAsSpeaker):
        self._showSelectAsSpeaker = showSelectAsSpeaker

    def isSelectSpeakerMandatory(self):
        try:
            return self._selectSpeakerMandatory
        except:
            self._selectSpeakerMandatory = True
            return self._selectSpeakerMandatory

    def setSelectSpeakerMandatory(self, selectSpeakerMandatory):
        self._selectSpeakerMandatory = selectSpeakerMandatory

    def showAttachedFilesContribList(self):
        try:
            return self._showAttachedFilesContribList
        except:
            self._showAttachedFilesContribList = False
            return self._showAttachedFilesContribList

    def setSwitchShowAttachedFilesContribList(self, showshowAttachedFilesContribList):
        self._showAttachedFilesContribList = showshowAttachedFilesContribList

    def getAbstractFieldsMgr(self):
        try:
            return self._abstractFieldsMgr
        except:
            self._abstractFieldsMgr = AbstractFieldsMgr()
            return self._abstractFieldsMgr

    def clone(self, conference):
        amgr = AbstractMgr(conference)
        amgr._abstractFieldsMgr = self.getAbstractFieldsMgr().clone()
        amgr.setAnnouncement(self.getAnnouncement())

        timeDifference = conference.getStartDate() - self.getOwner().getStartDate()
        amgr.setStartSubmissionDate(self.getStartSubmissionDate() + timeDifference)
        amgr.setEndSubmissionDate(self.getEndSubmissionDate() + timeDifference)

        modifDeadline = self.getModificationDeadline()
        if modifDeadline is not None:
            amgr.setModificationDeadline(self.getModificationDeadline() + timeDifference)

        amgr.setActive(self.isActive())
        if self.getCFAStatus():
            amgr.activeCFA()
        else:
            amgr.desactiveCFA()

        for a in self.getAbstractList():
            amgr.addAbstract(a.clone(conference, amgr._generateNewAbstractId()))

        for tpl in self.getNotificationTplList():
            amgr.addNotificationTpl(tpl.clone())

        # Cloning submission notification:
        amgr.setSubmissionNotification(self.getSubmissionNotification().clone())

        return amgr

    def getOwner(self):
        return self._owner
    getConference = getOwner

    def getTimezone(self):
        return self.getConference().getTimezone()

    def activeCFA(self):
        self._activated = True

    def desactiveCFA(self):
        self._activated = False

    def getAuthorizedSubmitterList(self):
        try:
            return self._authorizedSubmitter
        except AttributeError:
            self._authorizedSubmitter = PersistentList()
            return self._authorizedSubmitter

    def addAuthorizedSubmitter(self, av):
        try:
            if self._authorizedSubmitter:
                pass
        except AttributeError:
            self._authorizedSubmitter = PersistentList()
        if not av in self._authorizedSubmitter:
            self._authorizedSubmitter.append(av)
            av.linkTo(self, "abstractSubmitter")

    def removeAuthorizedSubmitter(self, av):
        try:
            if self._authorizedSubmitter:
                pass
        except:
            self._authorizedSubmitter = PersistentList()
        if av in self._authorizedSubmitter:
            self._authorizedSubmitter.remove(av)
            av.unlinkTo(self, "abstractSubmitter")

    def getCFAStatus(self):
        return self._activated

    def setActive(self, value):
        if value:
            self.activeCFA()
        else:
            self.desactiveCFA()

    def isActive(self):
        return self._activated

    def setStartSubmissionDate(self, date):
        self._submissionStartDate = datetime(date.year, date.month, date.day, 0, 0, 0)

    def getStartSubmissionDate(self):
        return timezone(self.getTimezone()).localize(self._submissionStartDate)

    def setEndSubmissionDate(self, date):
        self._submissionEndDate = datetime(date.year, date.month, date.day, 23, 59, 59)

    def getEndSubmissionDate(self):
        return timezone(self.getTimezone()).localize(self._submissionEndDate)

    def inSubmissionPeriod(self, date=None):
        if date is None:
            date = nowutc()
        sd = self.getStartSubmissionDate()
        ed = self.getEndSubmissionDate()
        return date <= ed and date >= sd

    def getModificationDeadline(self):
        """Returns the deadline for modifications on the submitted abstracts.
        """
        try:
            if self._modifDeadline:
                pass
        except AttributeError, e:
            self._modifDeadline = None
        if self._modifDeadline is not None:
            return timezone(self.getTimezone()).localize(self._modifDeadline)
        else:
            return None

    def setModificationDeadline(self, newDL):
        """Sets a new deadline for modifications on the submitted abstracts.
        """
        if newDL is not None:
            self._modifDeadline = datetime(newDL.year, newDL.month, newDL.day, 23, 59, 59)
        else:
            self._modifDeadline = newDL

    def inModificationPeriod(self, date=None):
        """Tells whether is possible to modify a submitted abstract in a
            certain date.
        """
        if date is None:
            date = nowutc()
        if not self.getModificationDeadline():
            return True
        return date <= self.getModificationDeadline()

    def getAnnouncement(self):
        #to be removed
        try:
            if self._announcement:
                pass
        except AttributeError, e:
            self._announcement = ""

        return self._announcement

    def setAnnouncement(self, newAnnouncement):
        self._announcement = newAnnouncement.strip()

##    def addContribType(self, type):
##        type = type.strip()
##        if type == "":
##            raise MaKaCError("Cannot add an empty contribution type")
##        self._contribTypes.append(type)
##
##    def removeContribType(self, type):
##        if type in self._contribTypes:
##            self._contribTypes.remove(type)
##
##    def getContribTypeList(self):
##        return self._contribTypes

    def _generateNewAbstractId(self):
        """Returns a new unique identifier for the current conference
            contributions
        """
        #instead of having a own counter, the abstract manager will request
        #   abstract ids to the conference which will ensure a unique id
        #   which will persist afterwards when an abstract is accepted
        return str(self.getConference().genNewAbstractId())

    def _getOldAbstractCounter(self):
        return self.__abstractGenerator._getCount()

    def newAbstract(self, av, **data):
        """Creates a new abstract under this manager
        """
        id = self._generateNewAbstractId()
        a = Abstract(self, id, av, **data)
        self._abstracts[id] = a
        for auth in a.getPrimaryAuthorList():
            self.indexAuthor(auth)
        return a

    def addAbstract(self, abstract):
        if abstract in self.getAbstractList():
            return
        if isinstance(abstract.getCurrentStatus(), AbstractStatusWithdrawn):
            raise MaKaCError(_("Cannot add an abstract which has been withdrawn"), ("Event"))
        abstract._setOwner(self)
        self._abstracts[abstract.getId()] = abstract
        for auth in abstract.getPrimaryAuthorList():
            self.indexAuthor(auth)

    def removeAbstract(self, abstract):
        if self._abstracts.has_key(abstract.getId()):
            #for auth in abstract.getPrimaryAuthorList():
            #    self.unindexAuthor(auth)
            # * Remove dependencies with another abstracts:
            #       - If it's an accepted abstract-->remove abstract from contribution
            if isinstance(abstract.getCurrentStatus(), AbstractStatusAccepted):
                raise NoReportError(_("Cannot remove an accepted abstract before removing the contribution linked to it"))
            # If it's a withdrawn abstract-->remove abstract from contribution
            if isinstance(abstract.getCurrentStatus(), AbstractStatusWithdrawn) and abstract.getContribution():
                raise NoReportError(_("Cannot remove the abstract before removing the contribution linked to it"))
            for abs in self._abstracts.values():
                if abs != abstract:
                    st = abs.getCurrentStatus()
                    if isinstance(st, AbstractStatusDuplicated):
                        #if the abstract to delete is the orginal in another "duplicated", change status to submitted
                        if st.getOriginal() == abstract:
                            abs.setCurrentStatus(AbstractStatusSubmitted(abs))
                    elif isinstance(st, AbstractStatusMerged):
                        #if the abstract to delete is the target one in another "merged", change status to submitted
                        if st.getTargetAbstract() == abstract:
                            abs.setCurrentStatus(AbstractStatusSubmitted(abs))
            #unindex participations!!!
            self.unregisterParticipation(abstract.getSubmitter())
            del self._abstracts[abstract.getId()]
            abstract.delete()

    def recoverAbstract(self, abstract):
        self.addAbstract(abstract)
        abstract.recoverFromTrashCan()

    def getAbstractList(self):
        return self._abstracts.values()

    def getAbstractById(self, id):
        return self._abstracts.get(str(id), None)

    def registerParticipation(self, p):
        self._participationIdx.index(p)

    def unregisterParticipation(self, p):
        self._participationIdx.unindex(p)

    def getAbstractListForAvatar(self, av):
        try:
            if self._participationIdx:
                pass
        except AttributeError, e:
            self._participationIdx = self._partipationIdx
            self._partipationIdx = None
        res = []
        for participation in self._participationIdx.getParticipationList(av):
            abstract = participation.getAbstract()
            if abstract is not None and abstract.isSubmitter(av):
                if abstract not in res:
                    res.append(abstract)
        return res

    def getAbstractListForAuthorEmail(self, email):
        """ Get list of abstracts where the email belongs to an author"""
        return [self.getAbstractById(i) for i in self._getAuthEmailIndex().match(email)]

    def getNotificationTplList(self):
        try:
            if self._notifTpls:
                pass
        except AttributeError:
            self._notifTpls = IOBTree()
        try:
            if self._notifTplsOrder:
                pass
        except AttributeError:
            self._notifTplsOrder = PersistentList()
            for tpl in self._notifTpls.values():
                self._notifTplsOrder.append(tpl)
        return self._notifTplsOrder

    def addNotificationTpl(self, tpl):
        try:
            if self._notifTpls:
                pass
        except AttributeError:
            self._notifTpls = IOBTree()
        try:
            if self._notifTplsOrder:
                pass
        except AttributeError:
            self._notifTplsOrder = PersistentList()
            for tpl in self._notifTpls.values():
                self._notifTplsOrder.append(tpl)
        try:
            if self._notifTplsCounter:
                pass
        except AttributeError:
            self._notifTplsCounter = Counter()
        if tpl.getOwner() == self and self._notifTpls.has_key(tpl.getId()):
            return
        id = tpl.getId()
        if id == "":
            id = self._notifTplsCounter.newCount()
        tpl.includeInOwner(self, id)
        self._notifTpls[int(id)] = tpl
        self._notifTplsOrder.append(tpl)

    def removeNotificationTpl(self, tpl):
        try:
            if self._notifTpls:
                pass
        except AttributeError:
            self._notifTpls = IOBTree()
        try:
            if self._notifTplsOrder:
                pass
        except AttributeError:
            self._notifTplsOrder = PersistentList()
            for tpl in self._notifTpls.values():
                self._notifTplsOrder.append(tpl)
        if tpl.getOwner() != self or not self._notifTpls.has_key(int(tpl.getId())):
            return
        del self._notifTpls[int(tpl.getId())]
        self._notifTplsOrder.remove(tpl)
        tpl.includeInOwner(None, tpl.getId())  # We don't change the id for
                                               # recovery purposes.
        tpl.delete()

    def recoverNotificationTpl(self, tpl):
        self.addNotificationTpl(tpl)
        tpl.recover()

    def getNotificationTplById(self, id):
        try:
            if self._notifTpls:
                pass
        except AttributeError:
            self._notifTpls = IOBTree()
        return self._notifTpls.get(int(id), None)

    def getNotifTplForAbstract(self, abs):
        """
        """
        for tpl in self.getNotificationTplList():
            if tpl.satisfies(abs):
                return tpl
        return None

    def moveUpNotifTpl(self, tpl):
        """
        """
        try:
            if self._notifTplsOrder:
                pass
        except AttributeError:
            self._notifTplsOrder = PersistentList()
            for tpl in self._notifTpls.values():
                self._notifTplsOrder.append(tpl)
        if tpl not in self._notifTplsOrder:
            return
        idx = self._notifTplsOrder.index(tpl)
        if idx == 0:
            return
        self._notifTplsOrder.remove(tpl)
        self._notifTplsOrder.insert(idx-1, tpl)

    def moveDownNotifTpl(self, tpl):
        """
        """
        try:
            if self._notifTplsOrder:
                pass
        except AttributeError:
            self._notifTplsOrder = PersistentList()
            for tpl in self._notifTpls.values():
                self._notifTplsOrder.append(tpl)
        idx = self._notifTplsOrder.index(tpl)
        if idx == len(self._notifTplsOrder):
            return
        self._notifTplsOrder.remove(tpl)
        self._notifTplsOrder.insert(idx+1, tpl)

    def indexAuthor(self, auth):
        a = auth.getAbstract()
        if a.isPrimaryAuthor(auth):
            self._getPrimAuthIndex().index(auth)
        self._getAuthEmailIndex().index(auth)

    def unindexAuthor(self, auth):
        a = auth.getAbstract()
        if a.isPrimaryAuthor(auth):
            self._getPrimAuthIndex().unindex(auth)
        self._getAuthEmailIndex().unindex(auth)

    def _getPrimAuthIndex(self):
        try:
            if self._primAuthIdx:
                pass
        except AttributeError:
            self._primAuthIdx = _PrimAuthIdx(self)
        return self._primAuthIdx

    def _getAuthEmailIndex(self):
        if not hasattr(self, '_authEmailIdx'):
            self._authEmailIdx = _AuthEmailIdx(self)
        return self._authEmailIdx

    def getAbstractsMatchingAuth(self, query, onlyPrimary=True):
        if str(query).strip() == "":
            return self.getAbstractList()
        res = self._getPrimAuthIndex().match(query)
        return [self.getAbstractById(id) for id in res]

    def setAbstractField(self, params):
        return self.getAbstractFieldsMgr().setField(params)

    def removeAbstractField(self, id):
        self.getAbstractFieldsMgr().removeField(id)

    def hasAnyEnabledAbstractField(self):
        return self.getAbstractFieldsMgr().hasAnyActiveField()

    def hasEnabledAbstractField(self, key):
        return self.getAbstractFieldsMgr().hasActiveField(key)

    def enableAbstractField(self, abstractField):
        self.getAbstractFieldsMgr().enableField(abstractField)
        self.notifyModification()

    def disableAbstractField(self, abstractField):
        self.getAbstractFieldsMgr().disableField(abstractField)
        self.notifyModification()

    def moveAbsFieldUp(self, id):
        self.getAbstractFieldsMgr().moveAbsFieldUp(id)
        self.notifyModification()

    def moveAbsFieldDown(self, id):
        self.getAbstractFieldsMgr().moveAbsFieldDown(id)
        self.notifyModification()

    def getSubmissionNotification(self):
        try:
            if self._submissionNotification:
                pass
        except AttributeError, e:
            self._submissionNotification = SubmissionNotification()
        return self._submissionNotification

    def setSubmissionNotification(self, sn):
        self._submissionNotification = sn

    def recalculateAbstractsRating(self, scaleLower, scaleHigher):
        ''' recalculate the values of the rating for all the abstracts in the conference '''
        for abs in self.getAbstractList():
            abs.updateRating((scaleLower, scaleHigher))

    def removeAnswersOfQuestion(self, questionId):
        ''' Remove a question results for each abstract '''
        for abs in self.getAbstractList():
            abs.removeAnswersOfQuestion(questionId)

    def notifyModification(self):
        self._p_changed = 1


class SubmissionNotification(Persistent):

    def __init__(self):
        self._toList = PersistentList()
        self._ccList = PersistentList()

    def hasDestination(self):
        return self._toList != [] or self._toList != []

    def getToList(self):
        return self._toList

    def setToList(self, tl):
        self._toList = tl

    def addToList(self, to):
        self._toList.append(to)

    def clearToList(self):
        self._toList = PersistentList()

    def getCCList(self):
        return self._ccList

    def setCCList(self, cl):
        self._ccList = cl

    def addCCList(self, cc):
        self._ccList.append(cc)

    def clearCCList(self):
        self._ccList = PersistentList()

    def clone(self):
        nsn = SubmissionNotification()
        for i in self.getToList():
            nsn.addToList(i)
        for i in self.getCCList():
            nsn.addCCList(i)
        return nsn


class Comment(Persistent):

    def __init__(self, res, content=""):
        self._abstract = None
        self._id = ""
        self._responsible = res
        self._content = ""
        self._creationDate = nowutc()
        self._modificationDate = nowutc()

    def getLocator(self):
        loc = self._abstract.getLocator()
        loc["intCommentId"] = self._id
        return loc

    def includeInAbstract(self, abstract, id):
        self._abstract = abstract
        self._id = id

    def delete(self):
        self._abstract = None
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def _notifyModification(self, dt=None):
        if dt:
            self._modificationDate = dt
        else:
            self._modificationDate = nowutc()

    def getResponsible(self):
        return self._responsible

    def getAbstract(self):
        return self._abstract

    def getId(self):
        return self._id

    def getContent(self):
        return self._content

    def setContent(self, newContent):
        self._content = newContent
        self._notifyModification()

    def getCreationDate(self):
        return self._creationDate

    def getModificationDate(self):
        return self._modificationDate

    def canModify(self, aw):
        return self.canUserModify(aw.getUser())

    def canUserModify(self, user):
        abstract = self.getAbstract()
        conf = abstract.getConference()
        return self.getResponsible() == user and \
            (abstract.canUserModify(user) or \
            len(conf.getConference().getCoordinatedTracks(user)) > 0)


class Abstract(Persistent):

    def __init__(self, owner, id, submitter, **abstractData):
        self._setOwner( owner )
        self._setId( id )
        self._title = ""
        self._fields = {}
        self._authorGen = Counter()
        self._authors = OOBTree()
        self._primaryAuthors = PersistentList()
        self._coAuthors = PersistentList()
        self._speakers = PersistentList()
        self._tracks = OOBTree()
        self._contribTypes = PersistentList( [""] )
        self._setSubmissionDate( nowutc() )
        self._modificationDate = nowutc()
        self._currentStatus = AbstractStatusSubmitted( self )
        self._trackAcceptances = OOBTree()
        self._trackRejections = OOBTree()
        self._trackReallocations = OOBTree()
        self._trackJudgementsHistorical={}
        self._comments = ""
        self._contribution = None
        self._intCommentGen=Counter()
        self._intComments=PersistentList()
        self._mergeFromList = PersistentList()
        self._notifLog=NotificationLog(self)
        self._submitter=None
        self._setSubmitter( submitter )
        self._rating = None # It needs to be none to avoid the case of having the same value as the lowest value in the judgement
        self._attachments = {}
        self._attachmentsCounter = Counter()

    def __cmp__(self, other):
        if type(self) is not type(other):
            # This is actually dangerous and the ZODB manual says not to do this
            # because it relies on memory order. However, this branch should never
            # be taken anyway since we do not store different types in the same set
            # or use them as keys.
            return cmp(hash(self), hash(other))
        if self.getConference() == other.getConference():
            return cmp(self.getId(), other.getId())
        return cmp(self.getConference(), other.getConference())

    def clone(self, conference, abstractId):

        # abstractId - internal in abstract manager of the conference
        abs = Abstract(conference.getAbstractMgr(), abstractId, self.getSubmitter().getAvatar())
        abs.setTitle(self.getTitle())
        for key in self.getFields().keys():
            abs.setField(key,self.getField(key))
        abs.setComments(self.getComments())

        abs._setSubmissionDate(self.getSubmissionDate())
        abs._modificationDate = self.getModificationDate()

        # Cloning of primary- and coauthors
        # if an author is also a speaker, an appropriate object will be
        # appended also to the speaker list
        for pa in self.getPrimaryAuthorList() :
            npa = abs.newPrimaryAuthor(**(pa.getData()))
            if self.isSpeaker(pa) :
                abs.addSpeaker(npa)
        for ca in self.getCoAuthorList() :
            nca = abs.newCoAuthor(**(ca.getData()))
            if self.isSpeaker(ca) :
                abs.addSpeaker(nca)

        # Cloning of speakers
        # only those, who are not authors :
            for sp in self.getSpeakerList() :
                if not self.isAuthor(sp) :
                    abs.addSpeaker(sp.clone())

        abs.setSubmitter(self.getSubmitter().getAvatar())

        if self.getContribType() is not None :
            for ct in conference.getContribTypeList() :
                if self.getContribType().getName() == ct.getName() :
                    abs.setContribType(ct)
                    break
        else :
            abs.setContribType(None)

        # the track, to which the abstract belongs to
        # legacy list implementation
        for tr in self.getTrackList() :
            for newtrack in conference.getTrackList():
                if newtrack.getTitle() == tr.getTitle() :
                    abs.addTrack(newtrack)

        # overall abstract status (accepted / rejected)
        abs._currentStatus = self._currentStatus.clone(abs)

        for ta in self.getTrackAcceptanceList() :
            for newtrack in conference.getTrackList():
                if newtrack.getTitle() == ta.getTrack().getTitle() :
                    newta = ta.clone(newtrack)
                    abs._addTrackAcceptance(newta)
                    abs._addTrackJudgementToHistorical(newta)

        for trj in self.getTrackRejections().values() :
            for newtrack in conference.getTrackList():
                if newtrack.getTitle() == trj.getTrack().getTitle() :
                    newtrj = trj.clone(newtrack)
                    abs._addTrackRejection(newtrj)
                    abs._addTrackJudgementToHistorical(newtrj)

        for trl in self.getTrackReallocations().values() :
            for newtrack in conference.getTrackList():
                if newtrack.getTitle() == trl.getTrack().getTitle() :
                    newtrl = trl.clone(newtrack)
                    abs._addTrackReallocation(newtrl)
                    abs._addTrackJudgementToHistorical(newtrl)

        # Cloning materials
        for f in self.getAttachments().values():
            newFile = f.clone(abs, protection=False)
            abs.__addFile(newFile)

        return abs

    def getUniqueId( self ):
        """returns (string) the unique identifier of the item"""
        """used only in the web session access key table"""
        """it is the same as the conference since only the conf can"""
        """be protected with an access key"""
        return self.getConference().getUniqueId()

    def getMergeFromList(self):
        try:
            return self._mergeFromList
        except AttributeError:
            self._mergeFromList = PersistentList()
            return self._mergeFromList

    def addMergeFromAbstract(self, abstract):
        try:
            if self._mergeFromList:
                pass
        except AttributeError:
            self._mergeFromList = PersistentList()
        self._mergeFromList.append(abstract)

    def removeMergeFromAbstract(self, abstract):
        try:
            if self._mergeFromList:
                pass
        except AttributeError:
            self._mergeFromList = PersistentList()

        if abstract in self._mergeFromList:
            self._mergeFromList.remove(abstract)

    def getComments(self):
        try:
            return self._comments
        except AttributeError:
            self._comments = ""
            return self._comments

    def setComments(self, comments):
        self._comments = comments

    def __addFile(self, file):
        file.archive(self.getConference()._getRepository())
        self.getAttachments()[file.getId()] = file
        self._notifyModification()


    def saveFiles(self, files):
        cfg = Config.getInstance()
        from MaKaC.conference import LocalFile
        for fileUploaded in files:
            if fileUploaded.filename:
                # create a temp file
                tempPath = cfg.getUploadedFilesTempDir()
                tempFileName = tempfile.mkstemp(suffix="IndicoAbstract.tmp", dir=tempPath)[1]
                f = open(tempFileName, "wb")
                f.write(fileUploaded.file.read() )
                f.close()
                file = LocalFile()
                file.setFileName(fileUploaded.filename)
                file.setFilePath(tempFileName)
                file.setOwner(self)
                file.setId(self._getAttachmentsCounter())
                self.__addFile(file)

    def deleteFilesNotInList(self, keys):
        """This method is used in order to delete all the files that are not present (by id) in the
        parameter "keys".
        This is useful when files are deleted from the abstract form using Javascript, and so it is
        the only way to know that they are deleted.
        """
        existingKeys = self.getAttachments().keys()
        for key in existingKeys:
            if not key in keys:
                self._deleteFile(key)

    def _deleteFile(self, key):
        file = self.getAttachments()[key]
        file.delete()
        del self.getAttachments()[key]
        self._notifyModification()

    def removeResource(self, res):
        """Necessary because LocalFile.delete (see _deleteFile) is calling this method.
        In our case, nothing to do.
        """
        pass

    def _setOwner( self, owner ):
        self._owner = owner

    def getOwner( self ):
        return self._owner

    def _setId( self, id ):
        self._id = str( id )

    def getId(self):
        return self._id

    def _setSubmissionDate( self, newDate ):
        self._submissionDate = newDate

    def setModificationDate(self, dt = None):
        if dt:
            self._modificationDate = dt
        else:
            self._modificationDate = nowutc()

    def _notifyModification( self, dt=None ):
        self.setModificationDate(dt)
        self._p_changed = 1

    def getModificationDate( self ):
        return self._modificationDate

    def _setSubmitter( self, av ):
        if not av:
            raise MaKaCError( _("An abstract must have a submitter"))
        if self._submitter:
            self.getOwner().unregisterParticipation( self._submitter )
            self._submitter.getUser().unlinkTo(self, "submitter")
            self._submitter.delete()
        self._submitter=Submitter( self, av )
        av.linkTo(self, "submitter")
        self.getOwner().registerParticipation( self._submitter )
        self._notifyModification()

    def recoverSubmitter(self, subm):
        if not subm:
            raise MaKaCError( _("An abstract must have a submitter"))
        if self._submitter:
            self.getOwner().unregisterParticipation( self._submitter )
            self._submitter.delete()
        self._submitter = subm
        self._submitter.setAbstract(self)
        self.getOwner().registerParticipation( self._submitter )
        subm.recover()
        self._notifyModification()

    def setSubmitter( self, av ):
        self._setSubmitter(av)

    def getSubmitter( self ):
        return self._submitter

    def isSubmitter( self, av ):
        return self.getSubmitter().representsUser( av )

    def setTitle(self, title):
        self._title = title.strip()
        self._notifyModification()

    def getTitle(self):
        return self._title

    def getFields(self):
        return self._fields

    def removeField(self, field):
        if self.getFields().has_key(field):
            del self.getFields()[field]
            self._notifyModification()

    def setField(self, fid, v):
        if isinstance(v, AbstractFieldContent):
            v = v.value
        try:
            self.getFields()[fid].value = v
            self._notifyModification()
        except:
            afm = self.getConference().getAbstractMgr().getAbstractFieldsMgr()
            f = next(f for f in afm.getFields() if f.getId() == fid)
            if f is not None:
                self.getFields()[fid] = AbstractFieldContent(f, v)

    def getField(self, field):
        if self.getFields().has_key(field):
            return self.getFields()[field]
        else:
            return ""

    def getSubmissionDate( self ):
        try:
            if self._submissionDate:
                pass
        except AttributeError:
            self._submissionDate=nowutc()
        return self._submissionDate

    def getConference( self ):
        mgr = self.getOwner()
        return mgr.getOwner() if mgr else None

    def _newAuthor( self, **data ):
        author = Author( self, **data )
        author.setId( self._authorGen.newCount() )
        self._authors[ author.getId() ] = author
        return author

    def _removeAuthor(self,part):
        if not self.isAuthor(part):
            return
        part.delete()
        del self._authors[part.getId()]

    def isAuthor( self, part ):
        return self._authors.has_key( part.getId() )

    def getAuthorList( self ):
        return self._authors.values()

    def getAuthorById(self, id):
        return self._authors.get(str(id), None)

    def clearAuthors( self ):
        self.clearPrimaryAuthors()
        self.clearCoAuthors()
        self._notifyModification()

    def newPrimaryAuthor(self,**data):
        auth=self._newAuthor(**data)
        self._addPrimaryAuthor(auth)
        self._notifyModification()
        return auth

    def isPrimaryAuthor( self, part ):
        return part in self._primaryAuthors

    def getPrimaryAuthorList( self ):
        return self._primaryAuthors
    #XXX: I keep it for compatibility but it should be removed
    getPrimaryAuthorsList = getPrimaryAuthorList

    def getPrimaryAuthorEmailList(self, lower=False):
        emailList = []
        for pAuthor in self.getPrimaryAuthorList():
            emailList.append(pAuthor.getEmail().lower() if lower else pAuthor.getEmail())
        return emailList

    def clearPrimaryAuthors(self):
        while len(self._primaryAuthors)>0:
            self._removePrimaryAuthor(self._primaryAuthors[0])
        self._notifyModification()

    def _addPrimaryAuthor( self, part ):
        if not self.isAuthor( part ):
            raise MaKaCError( _("The participation you want to set as primary author is not an author of the abstract"))
        if part in self._primaryAuthors:
            return
        self._primaryAuthors.append( part )
        self.getOwner().indexAuthor(part)

    def _removePrimaryAuthor(self,part):
        if not self.isPrimaryAuthor(part):
            return
        if self.isSpeaker(part):
            self.removeSpeaker(part)
        self.getOwner().unindexAuthor(part)
        self._primaryAuthors.remove(part)
        self._removeAuthor(part)

    def recoverPrimaryAuthor(self, auth):
        self._authors[ auth.getId() ] = auth
        auth.setAbstract(self)
        self._addPrimaryAuthor(auth)
        auth.recover()
        self._notifyModification()

    def newCoAuthor(self,**data):
        auth=self._newAuthor(**data)
        self._addCoAuthor(auth)
        self._notifyModification()
        return auth

    def _comp_CoAuthors(self):
        try:
            if self._coAuthors!=None:
                return
        except AttributeError:
            self._coAuthors=PersistentList()
        for auth in self._authors.values():
            if not self.isPrimaryAuthor(auth):
                self._addCoAuthor(auth)

    def isCoAuthor( self, part ):
        self._comp_CoAuthors()
        return part in self._coAuthors

    def getCoAuthorList( self ):
        self._comp_CoAuthors()
        return self._coAuthors

    def getCoAuthorEmailList(self, lower=False):
        emailList = []
        for coAuthor in self.getCoAuthorList():
            emailList.append(coAuthor.getEmail().lower() if lower else coAuthor.getEmail())
        return emailList

    def clearCoAuthors(self):
        while len(self._coAuthors)>0:
            self._removeCoAuthor(self._coAuthors[0])
        self._notifyModification()

    def _addCoAuthor( self, part ):
        self._comp_CoAuthors()
        if not self.isAuthor( part ):
            raise MaKaCError( _("The participation you want to set as primary author is not an author of the abstract"))
        if part in self._coAuthors:
            return
        self._coAuthors.append( part )

    def _removeCoAuthor(self,part):
        if not self.isCoAuthor(part):
            return
        if self.isSpeaker(part):
            self.removeSpeaker(part)
        self._coAuthors.remove(part)
        self._removeAuthor(part)

    def recoverCoAuthor(self, auth):
        self._authors[ auth.getId() ] = auth
        auth.setAbstract(self)
        self._addCoAuthor(auth)
        auth.recover()
        self._notifyModification()

    def addSpeaker( self, part ):
        if not self.isAuthor( part ):
            raise MaKaCError( _("The participation you want to set as speaker is not an author of the abstract"))
        if part in self._speakers:
            return
        self._speakers.append( part )
        self._notifyModification()

    def removeSpeaker(self,part):
        if part not in self._speakers:
            return
        self._speakers.remove(part)

    def clearSpeakers( self ):
        while len(self.getSpeakerList()) > 0:
            self.removeSpeaker(self.getSpeakerList()[0])
        self._speakers = PersistentList()

    def getSpeakerList( self ):
        return self._speakers

    def isSpeaker( self, part ):
        return part in self._speakers

    def setContribType( self, contribType ):
        self._contribTypes[0] = contribType
        self._notifyModification()

    def getContribType( self ):
        return self._contribTypes[0]


    def _addTrack( self, track ):
        """Adds the specified track to the suggested track list. Any
            verification must be done by the caller.
        """
        self._tracks[ track.getId() ] = track
        track.addAbstract( self )
        self._notifyModification()

    def addTrack( self, track ):
        self._changeTracksImpl()
        if not self._tracks.has_key( track.getId() ):
            self._addTrack( track )
            self.getCurrentStatus().update()

    def _removeTrack( self, track ):
        """Removes the specified track from the track list. Any verification
            must be done by the caller.
        """
        del self._tracks[ track.getId() ]
        track.removeAbstract( self )
        self._notifyModification()

    def removeTrack( self, track ):
        if self._tracks.has_key( track.getId() ):
            self._removeTrack( track )
            self.getCurrentStatus().update()
        if isinstance(self.getCurrentStatus(), AbstractStatusAccepted):
            self.getCurrentStatus()._setTrack(None)

    def _changeTracksImpl( self ):
        if self._tracks.__class__ != OOBTree:
            oldTrackList = self._tracks
            self._tracks = OOBTree()
            for track in oldTrackList:
                self._addTrack( track )
            self.getCurrentStatus().update()

    def getTrackList( self ):
        self._changeTracksImpl()

        return self._tracks.values()

    def hasTrack( self, track ):
        self._changeTracksImpl()

        return self._tracks.has_key( track.getId() )

    def getTrackListSorted( self ):
        self._changeTracksImpl()
        return self.getConference().sortTrackList( self._tracks.values() )

    def clearTracks( self ):
        self._changeTracksImpl()

        while len(self.getTrackList())>0:
            track = self.getTrackList()[0]
            self._removeTrack( track )
        self.getCurrentStatus().update()

    def setTracks( self, trackList ):
        """Set the suggested track classification of the current abstract to
            the specified list
        """
        #We need to do it in 2 steps otherwise the list over which we are
        #   iterating gets modified
        toBeRemoved = []
        toBeAdded = copy( trackList )
        for track in self.getTrackList():
            if track not in trackList:
                toBeRemoved.append( track )
            else:
                toBeAdded.remove( track )
        for track in toBeRemoved:
            self._removeTrack( track )
        for track in toBeAdded:
            self._addTrack( track )
        self.getCurrentStatus().update()

    def isProposedForTrack( self, track ):
        return self._tracks.has_key( track.getId() )

    def getNumTracks(self):
        return len( self._tracks )

    def getLocator(self):
        loc = self.getConference().getLocator()
        loc["abstractId"] = self.getId()
        return loc

    def isAllowedToCoordinate(self, av):
        """Tells whether or not the specified user can coordinate any of the
            tracks of this abstract
        """
        for track in self.getTrackList():
            if track.canUserCoordinate(av):
                return True
        return False

    def canAuthorAccess(self, user):
        if user is None:
            return False
        el = self.getCoAuthorEmailList(True)+self.getPrimaryAuthorEmailList(True)
        for e in user.getEmails():
            if e.lower() in el:
                return True
        return False

    def isAllowedToAccess(self, av):
        """Tells whether or not an avatar can access an abstract independently
            of the protection
        """
        #any author is allowed to access
        #CFA managers are allowed to access
        #any user being able to modify is also allowed to access
        #any TC is allowed to access
        if self.canAuthorAccess(av):
            return True
        if self.isAllowedToCoordinate(av):
            return True
        return self.canUserModify(av)

    def canAccess(self, aw):
        #if the conference is protected, then only allowed AW can access
        return self.isAllowedToAccess(aw.getUser())

    def canView(self, aw):
        #in the future it would be possible to add an access control
        #only those users allowed to access are allowed to view
        return self.isAllowedToAccess(aw.getUser())

    def canModify(self, aw):
        return self.canUserModify(aw.getUser())

    def canUserModify(self, av):
        #the submitter can modify
        if self.isSubmitter(av):
            return True
        #??? any CFA manager can modify
        #??? any user granted with modification privileges can modify
        #conference managers can modify
        conf = self.getConference()
        return conf.canUserModify(av)

    def getModifKey(self):
        return ""

    def getAccessKey(self):
        return ""

    def getAccessController(self):
        return self.getConference().getAccessController()

    def isProtected(self):
        return self.getConference().isProtected()

    def delete(self):
        if self._owner:
            self.getOwner().unregisterParticipation(self._submitter)
            self._submitter.getUser().unlinkTo(self, "submitter")
            self._submitter.delete()
            self._submitter = None
            self.clearAuthors()
            self.clearSpeakers()
            self.clearTracks()
            owner = self._owner
            self._owner = None
            owner.removeAbstract(self)
            self.setCurrentStatus(AbstractStatusNone(self))
            TrashCanManager().add(self)

    def recoverFromTrashCan(self):
        TrashCanManager().remove(self)

    def getCurrentStatus(self):
        try:
            if self._currentStatus:
                pass
        except AttributeError, e:
            self._currentStatus = AbstractStatusSubmitted(self)
        return self._currentStatus

    def setCurrentStatus(self, newStatus):
        self._currentStatus = newStatus
        #If we want to keep a history of status changes we should add here
        #   the old status to a list

    def accept(self, responsible, destTrack, type, comments="", session=None):
        """
        """
        self.getCurrentStatus().accept(responsible, destTrack, type, comments)
        #add the abstract to the track for which it has been accepted so it
        #   is visible for it.
        if destTrack is not None:
            destTrack.addAbstract(self)
        #once the abstract is accepted a new contribution under the destination
        #   track must be created
        # ATTENTION: This import is placed here explicitely for solving
        #   problems with circular imports
        from MaKaC.conference import AcceptedContribution
        contrib = AcceptedContribution(self)
        if session:
            contrib.setSession(session)
            contrib.setDuration(dur=session.getContribDuration())
        else:
            contrib.setDuration()
        self.getCurrentStatus().setContribution(contrib)
        self._setContribution(contrib)

    def reject(self, responsible, comments=""):
        """
        """
        self.getCurrentStatus().reject(responsible, comments)

    def _cmpByDate(self, tj1, tj2):
        return cmp(tj1.getDate(), tj2.getDate())

    def getTrackJudgementsHistorical(self):
        try:
            if self._trackJudgementsHistorical:
                pass
            if type(self._trackJudgementsHistorical) == tuple:
                self._trackJudgementsHistorical = {}
        except AttributeError:
            self._trackJudgementsHistorical = {}
            for track in self.getTrackList():
                judgement = None
                if self.getTrackAcceptances().has_key(track.getId()):
                    judgement = self.getTrackAcceptances()[track.getId()]
                elif self.getTrackRejections().has_key(track.getId()):
                    judgement = self.getTrackRejections()[track.getId()]
                elif self.getTrackReallocations().has_key(track.getId()):
                    judgement = self.getTrackReallocations()[track.getId()]
                self._trackJudgementsHistorical[track.getId()] = [judgement]
            self._notifyModification()
        return self._trackJudgementsHistorical

    def getJudgementHistoryByTrack(self, track):
        id = "notrack"
        if track is not None:
            id = track.getId()
        if self.getTrackJudgementsHistorical().has_key(id):
            return self.getTrackJudgementsHistorical()[id]
        return []

    def _addTrackJudgementToHistorical(self, tj):
        id = "notrack"
        if tj.getTrack() is not None:
            id = tj.getTrack().getId()
        if self.getTrackJudgementsHistorical().has_key(id):
            if tj not in self.getTrackJudgementsHistorical()[id]:
                self.getTrackJudgementsHistorical()[id].insert(0, tj)
        else:
            self.getTrackJudgementsHistorical()[id] = [tj]
        self._notifyModification()

    def _removeTrackAcceptance( self, track ):
        """
        """
        if self.getTrackAcceptances().has_key( track.getId() ):
            del self.getTrackAcceptances()[ track.getId() ]

    def _addTrackAcceptance( self, judgement ):
        """
        """
        self._removeTrackRejection( judgement.getTrack() )
        self._removeTrackReallocation( judgement.getTrack() )
        self.getTrackAcceptances()[ judgement.getTrack().getId() ] = judgement
        self._addTrackJudgementToHistorical(judgement)

    def _removeTrackRejection( self, track ):
        """
        """
        if self.getTrackRejections().has_key( track.getId() ):
            del self.getTrackRejections()[ track.getId() ]

    def _addTrackRejection( self, judgement ):
        """
        """
        self._removeTrackAcceptance( judgement.getTrack() )
        self._removeTrackReallocation( judgement.getTrack() )
        self.getTrackRejections()[ judgement.getTrack().getId() ] = judgement
        self._addTrackJudgementToHistorical(judgement)

    def _removeTrackReallocation( self, track ):
        """
        """
        if self.getTrackReallocations().has_key( track.getId() ):
            del self.getTrackReallocations()[ track.getId() ]

    def _addTrackReallocation( self, judgement ):
        """
        """
        self._removeTrackAcceptance( judgement.getTrack() )
        self._removeTrackRejection( judgement.getTrack() )
        self.getTrackReallocations()[ judgement.getTrack().getId() ] = judgement
        self._addTrackJudgementToHistorical(judgement)

    def _clearTrackRejections( self ):
        while len(self.getTrackRejections().values())>0:
            t = self.getTrackRejections().values()[0].getTrack()
            self._removeTrackRejection( t )

    def _clearTrackAcceptances( self ):
        while len(self.getTrackAcceptances().values())>0:
            t = self.getTrackAcceptances().values()[0].getTrack()
            self._removeTrackAcceptance( t )

    def _clearTrackReallocations( self ):
        while len(self.getTrackReallocations().values())>0:
            t = self.getTrackReallocations().values()[0].getTrack()
            self._removeTrackReallocation(t)

    def _removePreviousJud(self, responsible, track):
        ''' Check if there is a previous judgement and remove it '''
        toDelete = [] # list of judgements to delete
        for jud in self.getJudgementHistoryByTrack(track):
            if jud.getResponsible() == responsible:
                toDelete.append(jud)

        for x in toDelete:
            self.getTrackJudgementsHistorical()[track.getId()].remove(x)


    def proposeToAccept( self, responsible, track, contribType, comment="", answers=[] ):
        """
        """
        # the proposal has to be done for a track
        if track is None:
            raise MaKaCError( _("You have to choose a track in order to do the proposal. If there are not tracks to select, please change the track assignment of the abstract"))
        #We check the track for which the abstract is proposed to be accepted
        #   is in the current abstract
        if not self.isProposedForTrack( track ):
            raise MaKaCError( _("Cannot propose to accept an abstract which is not proposed for the specified track"))
        # check if there is a previous judgement of this author in for this abstract in this track
        self._removePreviousJud(responsible, track)
        # Create the new judgement
        jud = AbstractAcceptance( track, responsible, contribType, answers )
        jud.setComment( comment )
        self._addTrackAcceptance( jud )
        # Update the rating of the abstract
        self.updateRating()
        #We trigger the state transition
        self.getCurrentStatus().proposeToAccept()

    def proposeToReject( self, responsible, track, comment="", answers=[] ):
        """
        """
        # the proposal has to be done for a track
        if track is None:
            raise MaKaCError( _("You have to choose a track in order to do the proposal. If there are not tracks to select, please change the track assignment of the abstract"))
        #We check the track for which the abstract is proposed to be accepted
        #   is in the current abstract
        if not self.isProposedForTrack( track ):
            raise MaKaCError( _("Cannot propose to reject an abstract which is not proposed for the specified track"))
        # check if there is a previous judgement of this author in for this abstract in this track
        self._removePreviousJud(responsible, track)
        # Create the new judgement
        jud = AbstractRejection( track, responsible, answers )
        jud.setComment( comment )
        self._addTrackRejection( jud )
        # Update the rating of the abstract
        self.updateRating()
        #We trigger the state transition
        self.getCurrentStatus().proposeToReject()

    def proposeForOtherTracks( self, responsible, track, comment, propTracks, answers=[] ):
        """
        """
        #We check the track which proposes to allocate the abstract is in the
        #   current abstract
        if not self.isProposedForTrack( track ):
            raise MaKaCError( _("Cannot propose to reallocate an abstract which is not proposed for the specified track"))
        # check if there is a previous judgement of this author in for this abstract in this track
        self._removePreviousJud(responsible, track)
        #We keep the track judgement
        jud = AbstractReallocation( track, responsible, propTracks, answers )
        jud.setComment( comment )
        self._addTrackReallocation( jud )
        #We add the proposed tracks to the abstract
        for track in propTracks:
            self._addTrack( track )
        #We trigger the state transition
        self.getCurrentStatus().proposeToReallocate()
        # Update the rating of the abstract
        self.updateRating()

    def withdraw(self,resp,comment=""):
        """
        """
        self.getCurrentStatus().withdraw(resp,comment)

    def recover( self ):
        """Puts a withdrawn abstract back in the list of submitted abstracts.
           HAS NOTHING TO DO WITH THE RECOVERY PROCESS...
        """
        #we must clear any track judgement
        #self._clearTrackAcceptances()
        #self._clearTrackRejections()
        #self._clearTrackReallocations()
        self.getCurrentStatus().recover() #status change
        #if succeeded we must reset the submission date
        self._setSubmissionDate( nowutc() )
        self._notifyModification()

    def getTrackJudgement( self, track ):
        if not self.getJudgementHistoryByTrack(track):
            return None
        lastJud = self.getJudgementHistoryByTrack(track)[0]
        # check if judgements for specified trak are the same. If not there is a conflict.
        if all(jud.__class__ == lastJud.__class__ for jud in self.getJudgementHistoryByTrack(track)):
            return lastJud
        return AbstractInConflict(track)

    def getTrackAcceptances( self ):
        try:
            if self._trackAcceptances:
                pass
        except AttributeError, e:
            self._trackAcceptances = OOBTree()
        return self._trackAcceptances

    def getTrackAcceptanceList( self ):
        res = []
        for trackId in intersection( self._tracks, self.getTrackAcceptances() ):
            res.append( self.getTrackAcceptances()[ trackId ] )
        return res

    def getNumProposedToAccept( self ):
        return len( intersection( self._tracks, self.getTrackAcceptances() ) )

    def getTrackRejections( self ):
        try:
            if self._trackRejections:
                pass
        except AttributeError, e:
            self._trackRejections = OOBTree()
        return self._trackRejections

    def getNumProposedToReject( self ):
        return len( intersection( self._tracks, self.getTrackRejections() ) )

    def getTrackReallocations( self ):
        try:
            if self._trackReallocations:
                pass
        except AttributeError, e:
            self._trackReallocations = OOBTree()
        return self._trackReallocations


    def getNumProposedToReallocate( self ):
        return len( intersection( self._tracks, self.getTrackReallocations() ) )


    def getNumJudgements( self ):
        """
        Returns the number of tracks for which some proposal has been done.
        For instance, let's suppose:
           Track 1: 2 propose to accept, 3 propose to reject
           Track 2: 1 propose to accept
           Track 3: None
        The result would be 2 (out of 3)
        """
        tmp1 = union( self.getTrackAcceptances(), self.getTrackRejections() )
        judgements = union( tmp1, self.getTrackReallocations() )
        return len( intersection( self._tracks, judgements ) )

    def getReallocationTargetedList( self, track ):
        #XXX: not optimal
        res = []
        for r in self.getTrackReallocations().values():
            if track in r.getProposedTrackList():
                res.append( r )
        return res

    def getContribution( self ):
        try:
            if self._contribution:
                pass
        except AttributeError:
            self._contribution = None
        status = self.getCurrentStatus()
        if isinstance(status,AbstractStatusAccepted) and \
                                            self._contribution is None:
            self._contribution=status.getContribution()
        return self._contribution

    def _setContribution(self,contrib):
        self._contribution = contrib

    def getIntCommentList(self):
        try:
            if self._intComments:
                pass
        except AttributeError:
            self._intComments=PersistentList()
        return self._intComments

    def addIntComment(self,newComment):
        try:
            if self._intComments:
                pass
        except AttributeError:
            self._intComments=PersistentList()
        try:
            if self._intCommentsGen:
                pass
        except AttributeError:
            self._intCommentsGen=Counter()
        if newComment in self._intComments:
            return
        id = newComment.getId()
        if id == "":
            id = self._authorGen.newCount()
        newComment.includeInAbstract(self, id)
        self._intComments.append(newComment)

    def getIntCommentById(self,id):
        try:
            if self._intComments:
                pass
        except AttributeError:
            self._intComments=PersistentList()
        for comment in self._intComments:
            if id.strip()==comment.getId():
                return comment
        return None

    def clearIntCommentList(self):
        while len(self.getIntCommentList()) > 0:
            self.removeIntComment(self.getIntCommentList()[0])

    def removeIntComment(self,comment):
        try:
            if self._intComments:
                pass
        except AttributeError:
            self._intComments=PersistentList()
        if comment not in self._intComments:
            return
        self._intComments.remove(comment)
        comment.delete()

    def recoverIntComment(self, comment):
        self.addIntComment(comment)
        comment.recover()

    def markAsDuplicated(self,responsible,originalAbstract,comments="", track=None, answers=[]):
        """
        """
        self.getCurrentStatus().markAsDuplicated(responsible,originalAbstract,comments)
        # check if there is a previous judgement of this author in for this abstract in this track
        self._removePreviousJud(responsible, track)

        if track is not None:
            jud = AbstractMarkedAsDuplicated( track, responsible, originalAbstract, answers )
            jud.setComment( comments )
            self._addTrackJudgementToHistorical(jud)
        else:
            for t in self.getTrackList():
                jud = AbstractMarkedAsDuplicated( t, responsible, originalAbstract, answers )
                jud.setComment( comments )
                self._addTrackJudgementToHistorical(jud)
        # Update the rating of the abstract
        self.updateRating()

    def unMarkAsDuplicated(self,responsible,comments="", track=None, answers=[]):
        """
        """

        #we must clear any track judgement
        self._clearTrackAcceptances()
        self._clearTrackRejections()
        self._clearTrackReallocations()
        #self.getCurrentStatus().recover() #status change
        self.getCurrentStatus().unMarkAsDuplicated(responsible,comments)

        # check if there is a previous judgement of this author in for this abstract in this track
        self._removePreviousJud(responsible, track)

        if track is not None:
            jud = AbstractUnMarkedAsDuplicated(track, responsible, answers )
            jud.setComment( comments )
            self._addTrackJudgementToHistorical(jud)
        else:
            for t in self.getTrackList():
                jud = AbstractUnMarkedAsDuplicated( t, responsible, answers )
                jud.setComment( comments )
                self._addTrackJudgementToHistorical(jud)
        # Update the rating of the abstract
        self.updateRating()
        self._notifyModification()

    def mergeInto(self,responsible,targetAbs,mergeAuthors=False,comments=""):
        """
        """
        self.getCurrentStatus().mergeInto(responsible,targetAbs,comments)
        targetAbs.addMergeFromAbstract(self)
        if mergeAuthors:
            #for auth in self.getAuthorList():
            #    newAuth=targetAbs.newAuthor()
            #    newAuth.setFromAbstractParticipation(auth)
            #    if self.isPrimaryAuthor(auth):
            #        targetAbs.addPrimaryAuthor(newAuth)
            for auth in self.getPrimaryAuthorList():
                newAuth=targetAbs.newPrimaryAuthor()
                newAuth.setFromAbstractParticipation(auth)
            for auth in self.getCoAuthorList():
                newAuth=targetAbs.newCoAuthor()
                newAuth.setFromAbstractParticipation(auth)

    def notify(self,notificator,responsible):
        """notifies the abstract responsibles with a matching template
        """
        tpl=self.getOwner().getNotifTplForAbstract(self)
        if not tpl:
            return
        notificator.notify(self,tpl)
        self.getNotificationLog().addEntry(NotifLogEntry(responsible,tpl))

    def unMerge(self,responsible,comments=""):
        #we must clear any track judgement
        self._clearTrackAcceptances()
        self._clearTrackRejections()
        self._clearTrackReallocations()
        self.getCurrentStatus().getTargetAbstract().removeMergeFromAbstract(self)
        self.getCurrentStatus().unMerge(responsible,comments)
        self._notifyModification()

    def getNotificationLog(self):
        try:
            if self._notifLog:
                pass
        except AttributeError:
            self._notifLog=NotificationLog(self)
        return self._notifLog

    # Rating methods
    def getRating(self):
        """ Get the average rating of the abstract """
        try:
            if self._rating:
                pass
        except AttributeError:
            self._rating = None
        return self._rating

    def updateRating(self, scale = None):
        """
            Update the average rating of the abstract which is calculated with the average of each judgement.
            If the scale (tuple with lower,higher) is passed, the judgement are re-adjusted to the new scale.
        """
        self._rating = None
        # calculate the total valoration
        judNum = 0
        ratingSum = 0
        for track in self.getTrackListSorted():
            for jud in self.getJudgementHistoryByTrack(track):
                if scale:
                    # calculate the new values for each judgement
                    scaleLower, scaleHigher = scale
                    jud.recalculateJudgementValues(scaleLower, scaleHigher)
                if jud.getJudValue() != None: # it means there is a numeric value for the judgement
                    ratingSum += jud.getJudValue()
                    judNum += 1
        # Calculate the average
        if judNum != 0:
            self._rating = float(ratingSum) / judNum

    def getQuestionsAverage(self):
        '''Get the list of questions answered in the reviews for an abstract '''
        dTotals = {} # {idQ1: total_value, idQ2: total_value ...}
        dTimes = {} # {idQ1: times_answered, idQ2: times_answered}
        for track in self.getTrackListSorted():
            for jud in self.getJudgementHistoryByTrack(track):
                for answer in jud.getAnswers():
                    # check if the question is in d and sum the answers value or insert in d the new question
                    if dTotals.has_key(answer.getQuestion().getText()):
                        dTotals[answer.getQuestion().getText()] += answer.getValue()
                        dTimes[answer.getQuestion().getText()] += 1
                    else: # first time
                        dTotals[answer.getQuestion().getText()] = answer.getValue()
                        dTimes[answer.getQuestion().getText()] = 1
        # get the questions average
        questionsAverage = {}
        for q, v in dTotals.iteritems():
            # insert the element and calculate the average for the value
            questionsAverage[q] = float(v)/dTimes[q]
        return questionsAverage

    def removeAnswersOfQuestion(self, questionId):
        ''' Remove the answers of the question with questionId value '''
        for track in self.getTrackListSorted():
            for jud in self.getJudgementHistoryByTrack(track):
                jud.removeAnswer(questionId)

    def getRatingPerReviewer(self, user, track):
        """
            Get the rating of the user for the abstract in the track given.
        """
        for jud in self.getJudgementHistoryByTrack(track):
            if (jud.getResponsible() == user):
                return jud.getJudValue()

    def getLastJudgementPerReviewer(self, user, track):
        """
        Get the last judgement of the user for the abstract in the track given.
        """
        for jud in self.getJudgementHistoryByTrack(track):
            if (jud.getResponsible() == user):
                return jud

    def _getAttachmentsCounter(self):
        try:
            if self._attachmentsCounter:
                pass
        except AttributeError:
            self._attachmentsCounter = Counter()
        return self._attachmentsCounter.newCount()

    def setAttachments(self, attachments):
        self._attachments = attachments

    def getAttachments(self):
        try:
            if self._attachments:
                pass
        except AttributeError:
            self._attachments = {}
        return self._attachments

    def getAttachmentById(self, id):
        return self.getAttachments().get(id, None)


class AbstractJudgement( Persistent ):
    """This class represents each of the judgements made by a track about a
        certain abstract. Each track for which an abstract is proposed can
        make a judgement proposing the abstract to be accepted or rejected.
        Different track judgements must be kept so the referees who have to
        take the final decission can overview different opinions from the
        track coordinators.
      Together with the judgement some useful information like the date when
        it was done and the user who did it will be kept.
    """

    def __init__( self, track, responsible, answers ):
        self._track = track
        self._setResponsible( responsible )
        self._date = nowutc()
        self._comment = ""
        self._answers = answers
        self._judValue = self.calculateJudgementAverage() # judgement average value
        self._totalJudValue = self.calculateAnswersTotalValue()


    def _setResponsible( self, newRes ):
        self._responsible = newRes

    def getResponsible( self ):
        return self._responsible

    def getDate( self ):
        return self._date

    def setDate(self, date):
        self._date = date

    def getTrack( self ):
        return self._track

    def setComment( self, newComment ):
        self._comment = newComment.strip()

    def getComment( self ):
        return self._comment

    def getAnswers(self):
        try:
            if self._answers:
                pass
        except AttributeError:
            self._answers = []
        return self._answers

    def calculateJudgementAverage(self):
        '''Calculate the average value of the given answers'''
        result = 0
        if (len(self.getAnswers()) != 0):
            # convert the values into float types
            floatList = [ans.getValue() for ans in self._answers]
            result = sum(floatList) / float(len(floatList)) # calculate the average
        else:
            # there are no questions
            result = None
        return result

    def getJudValue(self):
        try:
            if self._judValue:
                pass
        except AttributeError:
            self._judValue = self.calculateJudgementAverage() # judgement average value
        return self._judValue

    def getTotalJudValue(self):
        try:
            if self._totalJudValue:
                pass
        except AttributeError:
            self._totalJudValue = self.calculateAnswersTotalValue()
        return self._totalJudValue

    def calculateAnswersTotalValue(self):
        ''' Calculate the sum of all the ratings '''
        result = 0
        for ans in self.getAnswers():
            result += ans.getValue()
        return result

    def recalculateJudgementValues(self, scaleLower, scaleHigher):
        ''' Update the values of the judgement. This function is called when the scale is changed.'''
        for ans in self.getAnswers():
            ans.calculateRatingValue(scaleLower, scaleHigher)
        self._judValue = self.calculateJudgementAverage()
        self._totalJudValue = self.calculateAnswersTotalValue()

    def removeAnswer(self, questionId):
        ''' Remove the current answers of the questionId '''
        for ans in self.getAnswers():
            if ans.getQuestion().getId() == questionId:
                self._answers.remove(ans)
                self._notifyModification()

    def _notifyModification(self):
        self._p_changed = 1


class AbstractAcceptance( AbstractJudgement ):

    def __init__( self, track, responsible, contribType, answers ):
        AbstractJudgement.__init__( self, track, responsible, answers )
        self._contribType = contribType

    def clone(self,track):
        aa = AbstractAcceptance(track,self.getResponsible(), self.getContribType(), self.getAnswers())
        return aa

    def getContribType( self ):
        try:
            if self._contribType:
                pass
        except AttributeError, e:
            self._contribType = None
        return self._contribType


class AbstractRejection( AbstractJudgement ):

    def clone(self, track):
        arj = AbstractRejection(track,self.getResponsible(), self.getAnswers())
        return arj

class AbstractReallocation( AbstractJudgement ):

    def __init__( self, track, responsible, propTracks, answers ):
        AbstractJudgement.__init__( self, track, responsible, answers )
        self._proposedTracks = PersistentList( propTracks )

    def clone(self, track):
        arl = AbstractReallocation(track, self.getResponsible(), self.getProposedTrackList(), self.getAnswers())
        return arl

    def getProposedTrackList( self ):
        return self._proposedTracks

class AbstractInConflict( AbstractJudgement ):

    def __init__( self, track ):
        AbstractJudgement.__init__( self, track, None, '' )

    def clone(self, track):
        aic = AbstractInConflict(track, None, '')
        return aic

class AbstractMarkedAsDuplicated( AbstractJudgement ):

    def __init__( self, track, responsible, originalAbst, answers ):
        AbstractJudgement.__init__( self, track, responsible, answers )
        self._originalAbst=originalAbst

    def clone(self,track):
        amad = AbstractMarkedAsDuplicated(track,self.getResponsible(), self.getOriginalAbstract(), self.getAnswers())
        return amad

    def getOriginalAbstract(self):
        return self._originalAbst


class AbstractUnMarkedAsDuplicated( AbstractJudgement ):

    def clone(self,track):
        auad = AbstractUnMarkedAsDuplicated(track,self.getResponsible())
        return auad


class AbstractStatus( Persistent ):
    """This class represents any of the status in which an abstract can be.
        From the moment they are submitted (and therefore created), abstracts
        can go throuugh different status each having a different meaning.
       As there can be many status, the transitions between them are quite
        complex and as the system evolves we could require to add or delete
        new status the "Status" pattern is applied. This is the base class.
       Apart from giving information about the status of an abstract, this
        class is responsible to store information about how the status was
        reached (who provoke the transition, when, ...).
    """
    _name = ""

    def __init__( self, abstract ):
        self._setAbstract( abstract )
        self._setDate( nowutc() )

    def getName(self):
        return self._name

    def _setAbstract( self, abs ):
        self._abstract = abs

    def getAbstract( self ):
        return self._abstract

    def _setDate( self, date ):
        self._date = date

    def getDate( self ):
        return self._date

    def accept(self,responsible,destTrack,type,comments=""):
        """
        """
        s = AbstractStatusAccepted(self.getAbstract(),responsible,destTrack,type,comments)
        self.getAbstract().setCurrentStatus( s )

    def reject( self, responsible, comments = "" ):
        """
        """
        s = AbstractStatusRejected( self.getAbstract(), responsible, comments )
        self.getAbstract().setCurrentStatus( s )

    def _getStatusClass( self ):
        """
        """
        numAccepts = self._abstract.getNumProposedToAccept() # number of tracks that have at least one proposal to accept
        numReallocate = self._abstract.getNumProposedToReallocate() # number of tracks that have at least one proposal to reallocate
        numJudgements = self._abstract.getNumJudgements() # number of tracks that have at least one judgement
        if numJudgements > 0:
            # If at least one track status is in conflict the abstract status is in conflict too.
            if any(isinstance(self._abstract.getTrackJudgement(track), AbstractInConflict) for track in self._abstract.getTrackList()):
                return AbstractStatusInConflict
            numTracks = self._abstract.getNumTracks() # number of tracks that this abstract has assigned
            if numTracks == numJudgements: # Do we have judgements for all tracks?
                if numReallocate == numTracks:
                    return AbstractStatusInConflict
                elif numAccepts == 1:
                    return AbstractStatusProposedToAccept
                elif numAccepts == 0:
                    return AbstractStatusProposedToReject
                return AbstractStatusInConflict
            return AbstractStatusUnderReview
        return AbstractStatusSubmitted


    def update( self ):
        """
        """
        newStatusClass = self._getStatusClass()
        if self.__class__ != newStatusClass:
            self.getAbstract().setCurrentStatus( newStatusClass( self._abstract ) )

    def proposeToAccept( self ):
        """
        """
        s = self._getStatusClass()( self._abstract )
        self.getAbstract().setCurrentStatus( s )

    def proposeToReject( self ):
        """
        """
        s = self._getStatusClass()( self._abstract )
        self.getAbstract().setCurrentStatus( s )

    def proposeToReallocate( self ):
        """
        """
        s = self._getStatusClass()( self._abstract )
        self.getAbstract().setCurrentStatus( s )

    def withdraw(self,resp,comments=""):
        """
        """
        s=AbstractStatusWithdrawn(self.getAbstract(), resp, self, comments)
        self.getAbstract().setCurrentStatus(s)

    def recover( self ):
        """
        """
        raise MaKaCError( _("only withdrawn abstracts can be recovered"))

    def markAsDuplicated(self,responsible,originalAbs,comments=""):
        """
        """
        if self.getAbstract()==originalAbs:
            raise MaKaCError( _("the original abstract is the same as the duplicated one"))
        if isinstance(originalAbs.getCurrentStatus(),AbstractStatusDuplicated):
            raise MaKaCError( _("cannot set as original abstract one which is already marked as duplicated"))
        s=AbstractStatusDuplicated(self.getAbstract(),responsible,originalAbs,comments)
        self.getAbstract().setCurrentStatus(s)

    def unMarkAsDuplicated(self,responsible,comments=""):
        """
        """
        raise MaKaCError( _("Only duplicated abstract can be unmark as duplicated"))

    def mergeInto(self,responsible,targetAbs,comments=""):
        """
        """
        if self.getAbstract()==targetAbs:
            raise MaKaCError( _("An abstract cannot be merged into itself"))
        if targetAbs.getCurrentStatus().__class__ not in [AbstractStatusSubmitted,AbstractStatusUnderReview,AbstractStatusProposedToAccept,AbstractStatusProposedToReject,AbstractStatusInConflict]:
            raise MaKaCError(_("Target abstract is in a status which cannot receive mergings"))
        s=AbstractStatusMerged(self.getAbstract(),responsible,targetAbs,comments)
        self.getAbstract().setCurrentStatus(s)

    def unMerge(self,responsible,comments=""):
        """
        """
        raise MaKaCError( _("Only merged abstracts can be unmerged"))

    def getComments(self):
        return ""



class AbstractStatusSubmitted( AbstractStatus ):
    """
    """

    def clone(self,abstract):
        ass = AbstractStatusSubmitted(abstract)
        return ass

    def update( self ):
        #if an abstract that has been submitted has no judgement it
        #   must remain in the submitted status
        if self._abstract.getNumJudgements() == 0:
            return
        AbstractStatus.update( self )


class AbstractStatusAccepted( AbstractStatus ):
    """
    """
    def __init__(self,abstract,responsible,destTrack,type,comments=""):
        AbstractStatus.__init__( self, abstract )
        self._setResponsible( responsible )
        self._setTrack( destTrack )
        self._setComments( comments )
        self._setType( type )
        self._contrib = None

    def clone(self,abstract):
        asa = AbstractStatusAccepted(abstract,self.getResponsible(), self.getTrack(), self.getType(), self.getComments())
        return asa

    def _setResponsible( self, res ):
        self._responsible = res

    def getResponsible( self ):
        return self._responsible

    def _setComments( self, comments ):
        self._comments = str( comments ).strip()

    def getComments( self ):
        try:
            if self._comments:
                pass
        except AttributeError:
            self._comments = ""
        return self._comments

    def _setTrack( self, track ):
        self._track = track

    def getTrack( self ):
        try:
            if self._track:
                pass
        except AttributeError:
            self._track = None
        return self._track

    def _setType( self, type ):
        self._contribType = type

    def getType( self ):
        try:
            if self._contribType:
                pass
        except AttributeError:
            self._contribType = None
        return self._contribType

    def setContribution( self, newContrib ):
        self._contrib = newContrib

    def getContribution( self ):
        try:
            if self._contrib:
                pass
        except AttributeError:
            self._contrib = None
        return self._contrib

    def update( self ):
        return

    def accept(self,responsible,destTrack,type,comments="" ):
        raise MaKaCError( _("Cannot accept an abstract which is already accepted"))

    def reject( self, responsible, comments="" ):
        raise MaKaCError( _("Cannot reject an abstract which is already accepted"))

    def proposeToAccept( self ):
        raise MaKaCError( _("Cannot propose for acceptance an abstract which is already accepted"))

    def proposeToReject( self ):
        raise MaKaCError( _("Cannot propose for rejection an abstract which is already accepted"))

    def proposeToReallocate( self ):
        raise MaKaCError( _("Cannot propose for reallocation an abstract which is already accepted"))

    def markAsDuplicated(self,responsible,originalAbs,comments=""):
        raise MaKaCError( _("Cannot mark as duplicated an abstract which is accepted"))

    def unMarkAsDuplicated(self,responsible,comments=""):
        """
        """
        raise MaKaCError( _("Only duplicated abstract can be unmark as duplicated"))

    def mergeInto(self,responsible,targetAbs,comments=""):
        raise MaKaCError( _("Cannot merge an abstract which is already accepted"))

    def withdraw(self,resp,comments=""):
        """
        """
        contrib=self.getContribution()
        #this import is made here and not at the top of the file in order to
        #   avoid recursive import troubles
        from MaKaC.conference import ContribStatusWithdrawn
        if contrib is not None and \
                not isinstance(contrib.getCurrentStatus(),ContribStatusWithdrawn):
            contrib.withdraw(resp, i18nformat(""" _("abstract withdrawn"): %s""")%comments)
        AbstractStatus.withdraw(self,resp,comments)


class AbstractStatusRejected( AbstractStatus ):
    """
    """
    def __init__( self, abstract, responsible, comments = "" ):
        AbstractStatus.__init__( self, abstract )
        self._setResponsible( responsible )
        self._setComments( comments )

    def clone(self,abstract):
        asr = AbstractStatusRejected(abstract, self.getResponsible(), self.getComments())
        return asr

    def _setResponsible( self, res ):
        self._responsible = res

    def getResponsible( self ):
        return self._responsible

    def _setComments( self, comments ):
        self._comments = str( comments ).strip()

    def getComments( self ):
        try:
            if self._comments:
                pass
        except AttributeError:
            self._comments = ""
        return self._comments

    def update( self ):
        return

    def reject( self, responsible, comments="" ):
        raise MaKaCError(  _("Cannot reject an abstract which is already rejected"))

    def proposeToAccept( self ):
        raise MaKaCError(  _("Cannot propose for acceptance an abstract which is already rejected"))

    def proposeToReject( self ):
        raise MaKaCError(  _("Cannot propose for rejection an abstract which is already rejected"))

    def proposeToReallocate( self ):
        raise MaKaCError(  _("Cannot propose for reallocation an abstract which is already rejected"))

    def withdraw(self,resp,comments=""):
        raise MaKaCError(  _("Cannot withdraw a REJECTED abstract"))

    def markAsDuplicated(self,responsible,originalAbs,comments=""):
        raise MaKaCError( _("Cannot mark as duplicated an abstract which is rejected"))

    def unMarkAsDuplicated(self,responsible,comments=""):
        """
        """
        raise MaKaCError( _("Only duplicated abstract can be unmark as duplicated"))

    def mergeInto(self,responsible,targetAbs,comments=""):
        raise MaKaCError( _("Cannot merge an abstract which is rejected"))


class AbstractStatusUnderReview( AbstractStatus ):
    """
    """
    def clone(self,abstract):
        asur = AbstractStatusUnderReview(abstract)
        return asur

class AbstractStatusProposedToAccept( AbstractStatus ):
    """
    """
    def clone(self, abstract):
        aspta = AbstractStatusProposedToAccept(abstract)
        return aspta

    def getTrack(self):
        jud=self.getAbstract().getTrackAcceptanceList()[0]
        return jud.getTrack()

    def getType(self):
        jud=self.getAbstract().getTrackAcceptanceList()[0]
        return jud.getContribType()


class AbstractStatusProposedToReject( AbstractStatus ):
    """
    """
    def clone(self, abstract):
        asptr = AbstractStatusProposedToReject(abstract)
        return asptr

class AbstractStatusInConflict( AbstractStatus ):
    """
    """
    def clone(self,abstract):
        asic = AbstractStatusInConflict(abstract)
        return asic

class AbstractStatusWithdrawn(AbstractStatus):
    """
    """
    def __init__(self,abstract,responsible, prevStatus,comments=""):
        AbstractStatus.__init__(self,abstract)
        self._setComments(comments)
        self._setResponsible(responsible)
        self._prevStatus=prevStatus

    def clone(self,abstract):
        asw = AbstractStatusWithdrawn(abstract,self.getResponsible(),self.getComments())
        return asw

    def _setResponsible(self,newResp):
        self._responsible=newResp

    def getResponsible(self):
        try:
            if self._responsible:
                pass
        except AttributeError,e:
            self._responsible=self._abstract.getSubmitter().getAvatar()
        return self._responsible

    def getPrevStatus(self):
        try:
            if self._prevStatus:
                pass
        except AttributeError,e:
            self._prevStatus=None
        return self._prevStatus

    def _setComments( self, comments ):
        self._comments = str( comments ).strip()

    def getComments( self ):
        return self._comments

    def update( self ):
        return

    def accept(self,responsible,destTrack,type,comments=""):
        raise MaKaCError( _("Cannot accept an abstract wich is withdrawn"))

    def reject( self, responsible, comments="" ):
        raise MaKaCError(  _("Cannot reject an abstract which is withdrawn"))

    def proposeToAccept( self ):
        raise MaKaCError(  _("Cannot propose for acceptance an abstract which withdrawn"))

    def proposeToReject( self ):
        raise MaKaCError(  _("Cannot propose for rejection an abstract which is withdrawn"))

    def recover( self ):
        if self.getPrevStatus() is None:
            # reset all the judgments
            self._clearTrackAcceptances()
            self._clearTrackRejections()
            self._clearTrackReallocations()
            # setting the status
            contrib=self.getAbstract().getContribution()
            if contrib is None:
                s = AbstractStatusSubmitted( self.getAbstract() )
            else:
                s = AbstractStatusAccepted(self.getAbstract(),self.getResponsible(),contrib.getTrack(),contrib.getType(),"")
        else:
            contrib=self.getAbstract().getContribution()
            if contrib is not None and not isinstance(self.getPrevStatus(), AbstractStatusAccepted):
                s = AbstractStatusAccepted(self.getAbstract(),self.getResponsible(),contrib.getTrack(),contrib.getType(),"")
            else:
                s=self.getPrevStatus()
        self.getAbstract().setCurrentStatus( s )

    def markAsDuplicated(self,responsible,originalAbs,comments=""):
        raise MaKaCError( _("Cannot mark as duplicated an abstract which is withdrawn"))

    def unMarkAsDuplicated(self,responsible,comments=""):
        """
        """
        raise MaKaCError( _("Only duplicated abstract can be unmark as duplicated"))

    def mergeInto(self,responsible,targetAbs,comments=""):
        raise MaKaCError( _("Cannot merge an abstract which is withdrawn"))

    def withdraw(self,resp,comments=""):
        raise MaKaCError( _("This abstract is already withdrawn"))



class AbstractStatusDuplicated(AbstractStatus):
    """
    """
    def __init__( self,abstract,responsible,originalAbstract,comments=""):
        AbstractStatus.__init__(self,abstract)
        self._setResponsible(responsible)
        self._setComments(comments)
        self._setOriginalAbstract(originalAbstract)

    def clone(self, abstract):
        asd = AbstractStatusDuplicated(abstract,self.getResponsible(),self.getOriginal(),self.getComments())
        return asd

    def _setResponsible( self, res ):
        self._responsible = res

    def getResponsible(self):
        return self._responsible

    def _setComments( self, comments ):
        self._comments = str( comments ).strip()

    def getComments( self ):
        return self._comments

    def _setOriginalAbstract(self,abs):
        self._original=abs

    def getOriginal(self):
        return self._original

    def update( self ):
        return

    def reject( self, responsible, comments="" ):
        raise MaKaCError( _("Cannot reject an abstract which is duplicated"))

    def proposeToAccept( self ):
        raise MaKaCError( _("Cannot propose for acceptance an abstract which is duplicated"))

    def proposeToReject( self ):
        raise MaKaCError( _("Cannot propose for rejection an abstract which is duplicated"))

    def proposeToReallocate( self ):
        raise MaKaCError( _("Cannot propose for reallocation an abstract which is duplicated"))

    def withdraw(self,resp,comments=""):
        raise MaKaCError( _("Cannot withdraw a duplicated abstract"))

    def markAsDuplicated(self,responsible,originalAbs,comments=""):
        raise MaKaCError( _("This abstract is already duplicated"))

    def unMarkAsDuplicated(self,responsible,comments=""):
        s = AbstractStatusSubmitted( self.getAbstract() )
        self.getAbstract().setCurrentStatus( s )

    def mergeInto(self,responsible,targetAbs,comments=""):
        raise MaKaCError( _("Cannot merge an abstract which is marked as a duplicate"))


class AbstractStatusMerged(AbstractStatus):
    """
    """

    def __init__(self,abstract,responsible,targetAbstract,comments=""):
        AbstractStatus.__init__(self,abstract)
        self._setResponsible(responsible)
        self._setComments(comments)
        self._setTargetAbstract(targetAbstract)

    def clone(self,abstract):
        asm = AbstractStatusMerged(abstract,self.getResponsible(),self.getTargetAbstract(),self.getComments())
        return asm

    def _setResponsible( self, res ):
        self._responsible = res

    def getResponsible( self ):
        return self._responsible

    def _setComments( self, comments ):
        self._comments = str( comments ).strip()

    def getComments( self ):
        return self._comments

    def _setTargetAbstract(self,abstract):
        self._target=abstract

    def getTargetAbstract(self):
        return self._target

    def update( self ):
        return

    def reject( self, responsible, comments="" ):
        raise MaKaCError( _("Cannot reject an abstract which is merged into another one"))

    def proposeToAccept( self ):
        raise MaKaCError( _("Cannot propose for acceptance an abstract which is merged into another one"))

    def proposeToReject( self ):
        raise MaKaCError( _("Cannot propose for rejection an abstract which is merged into another one"))

    def proposeToReallocate( self ):
        raise MaKaCError( _("Cannot propose for reallocation an abstract which is merged into another one"))

    def withdraw(self,resp,comments=""):
        raise MaKaCError( _("Cannot withdraw an abstract which is merged into another one"))

    def markAsDuplicated(self,responsible,originalAbs,comments=""):
        raise MaKaCError( _("Cannot mark as duplicated an abstract which is merged into another one"))

    def unMarkAsDuplicated(self,responsible,comments=""):
        """
        """
        raise MaKaCError( _("Only duplicated abstract can be unmark as duplicated"))

    def mergeInto(self,responsible,target,comments=""):
        raise MaKaCError( _("This abstract is already merged into another one"))

    def unMerge(self,responsible,comments=""):
        s = AbstractStatusSubmitted( self.getAbstract() )
        self.getAbstract().setCurrentStatus( s )

class AbstractStatusNone(AbstractStatus):
# This is a special status we assign to abstracts that are put in the trash can.

    def __init__(self,abstract):
        AbstractStatus.__init__(self,abstract)

    def clone(self,abstract):
        asn = AbstractStatusNone(abstract)
        return asn

class NotificationTemplate(Persistent):

    def __init__(self):
        self._owner=None
        self._id=""
        self._name=""
        self._description=""
        self._tplSubject=""
        self._tplBody=""
        self._fromAddr = ""
        self._CAasCCAddr = False
        self._ccAddrList=PersistentList()
        self._toAddrs = PersistentList()
        self._conditions=PersistentList()
        self._toAddrGenerator=Counter()
        self._condGenerator=Counter()

    def clone(self):
        tpl = NotificationTemplate()
        tpl.setName(self.getName())
        tpl.setDescription(self.getDescription())
        tpl.setTplSubject(self.getTplSubject())
        tpl.setTplBody(self.getTplBody())
        tpl.setFromAddr(self.getFromAddr())
        tpl.setCAasCCAddr(self.getCAasCCAddr())

        for cc in self.getCCAddrList() :
            tpl.addCCAddr(cc)
        for to in self.getToAddrList() :
            tpl.addToAddr(to)

        for con in self.getConditionList() :
            tpl.addCondition(con.clone(tpl))

        return tpl

    def delete(self):
        self.clearToAddrs()
        self.clearCCAddrList()
        self.clearConditionList()
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

##    def getResponsible( self ):
##        return self._responsible
##
##    def _setComments( self, comments ):
##        self._comments = str( comments ).strip()
##
##    def getComments( self ):
##        return self._comments
##
##    def _setOriginalAbstract(self,abstract):
##        self._original=abstract

    def canModify(self, aw):
        return self.getConference().canModify(aw)

    def getLocator(self):
        loc = self.getOwner().getConference().getLocator()
        loc["notifTplId"] = self._id
        return loc

    def getConference(self):
        return self._owner.getConference()

    def includeInOwner(self,owner,id):
        self._owner=owner
        self._id=id

    def getOwner(self):
        return self._owner

    def getId(self):
        return self._id

    def setName(self,newName):
        self._name=newName.strip()

    def getName(self):
        return self._name

    def setDescription(self,newDesc):
        self._description=newDesc.strip()

    def getDescription(self):
        return self._description

    def setTplSubject(self,newSubject, varList):
        self._tplSubject=self.parseTplContent(newSubject, varList).strip()

    def getTplSubject(self):
        return self._tplSubject

    def getTplSubjectShow(self, varList):
        return self.parseTplContentUndo(self._tplSubject, varList)

    def setTplBody(self,newBody, varList):
        self._tplBody=self.parseTplContent(newBody, varList).strip()

    def getTplBody(self):
        return self._tplBody

    def getTplBodyShow(self, varList):
        return self.parseTplContentUndo(self._tplBody, varList)

    def getCCAddrList(self):
        try:
            if self._ccAddrList:
                pass
        except AttributeError:
            self._ccAddrList=PersistentList()
        return self._ccAddrList

    def addCCAddr(self,newAddr):
        try:
            if self._ccAddrList:
                pass
        except AttributeError:
            self._ccAddrList=PersistentList()
        ccAddr=newAddr.strip()
        if ccAddr!="" and ccAddr not in self._ccAddrList:
            self._ccAddrList.append(ccAddr)

    def setCCAddrList(self,l):
        self.clearCCAddrList()
        for addr in l:
            self.addCCAddr(addr)

    def setCAasCCAddr(self, CAasCCAddr):
        self._CAasCCAddr = CAasCCAddr

    def getCAasCCAddr(self):
        try:
            if self._CAasCCAddr:
                pass
        except AttributeError:
            self._CAasCCAddr = False
        return self._CAasCCAddr

    def clearCCAddrList(self):
        self._ccAddrList=PersistentList()

    def getFromAddr(self):
        try:
            return self._fromAddr
        except AttributeError:
            self._fromAddr = self._owner.getConference().getSupportInfo().getEmail()
            return self._fromAddr

    def setFromAddr(self, addr):
        self._fromAddr = addr

    def addToAddr(self,toAddr):
        """
        """
        if self.hasToAddr(toAddr.__class__):
            return
        try:
            if self._toAddrGenerator:
                pass
        except AttributeError, e:
            self._toAddrGenerator =  Counter()
        id = toAddr.getId()
        if id == -1:
            id = int(self._toAddrGenerator.newCount())
        toAddr.includeInTpl(self,id)
        self.getToAddrList().append(toAddr)

    def removeToAddr(self,toAddr):
        """
        """
        if not self.hasToAddr(toAddr.__class__):
            return
        self.getToAddrList().remove(toAddr)
        toAddr.includeInTpl(None,toAddr.getId())
        toAddr.delete()

    def recoverToAddr(self, toAddr):
        self.addToAddr(toAddr)
        toAddr.recover()

    def getToAddrs(self, abs):
        users = []
        for toAddr in self.getToAddrList():
            users += toAddr.getToAddrList(abs)
        return users

    def getToAddrList(self):
        """
        """
        try:
            if self._toAddrs:
                pass
        except AttributeError, e:
            self._toAddrs = PersistentList()
        return self._toAddrs

    def getToAddrById(self,id):
        """
        """
        for toAddr in self.getToAddrList():
            if toAddr.getId()==int(id):
                return toAddr
        return None

    def hasToAddr(self,toAddrKlass):
        """Returns True if the TPL contains a "toAddr" which class is "toAddrKlass"
        """
        for toAddr in self.getToAddrList():
            if toAddr.__class__ == toAddrKlass:
                return True
        return False

    def clearToAddrs(self):
        while(len(self.getToAddrList())>0):
            self.removeToAddr(self.getToAddrList()[0])

    def addCondition(self,cond):
        """
        """
        if cond in self._conditions:
            return
        id = cond.getId()
        if id == -1:
            id = int(self._condGenerator.newCount())
        cond.includeInTpl(self, id)
        self._conditions.append(cond)

    def removeCondition(self,cond):
        """
        """
        if cond not in self._conditions:
            return
        self._conditions.remove(cond)
        cond.delete()

    def recoverCondition(self, cond):
        self.addCondition(cond)
        cond.recover()

    def getConditionList(self):
        """
        """
        return self._conditions

    def getConditionById(self,id):
        """
        """
        for cond in self._conditions:
            if cond.getId()==int(id):
                return cond
        return None

    def clearConditionList(self):
        while(len(self.getConditionList())>0):
            self.removeCondition(self.getConditionList()[0])

    def satisfies(self,abs):
        """
        """
        for cond in self._conditions:
            if cond.satisfies(abs):
                return True
        return False

    def parseTplContent(self, content, varList):
        # replace the % in order to avoid exceptions
        result = content.replace("%", "%%")
        # find the vars and make the expressions, it is necessary to do in reverse in order to find the longest tags first
        for var in varList:
            result = result.replace("{"+var.getName()+"}", "%("+var.getName()+")s")
        return result

    def parseTplContentUndo(self, content, varList):
        # The body content is shown without "%()" and with "%" in instead of "%%" but it is not modified
        result = content
        for var in varList:
            result = result.replace("%("+var.getName()+")s", "{"+var.getName()+"}")
        # replace the %% by %
        result = result.replace("%%", "%")
        return result

    def getModifKey( self ):
        return self.getConference().getModifKey()



class NotifTplToAddr(Persistent):
    """
    """

    def __init__(self):
        self._tpl=None
        self._id=-1

    def clone(self):
        ntta = NotifTplToAddr()
        return ntta

    def delete(self):
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def includeInTpl(self,newTpl,newId):
        self._tpl=newTpl
        self._id=newId

    def getTpl(self):
        return self._tpl

    def getId(self):
        return self._id

    def getToAddrList(self,absList):
        """
        Return a list with all the emails for a group.
        """
        return []


class NotifTplToAddrSubmitter(NotifTplToAddr):

    def getToAddrList(self,abs):
        l = []
        l.append(abs.getSubmitter())
        return l

    def clone(self):
        nttas = NotifTplToAddrSubmitter()
        return nttas

class NotifTplToAddrPrimaryAuthors(NotifTplToAddr):

    def getToAddrList(self,abs):
        l = []
        for pa in abs.getPrimaryAuthorList():
            l.append(pa)
        return l

    def clone(self):
        nttapa = NotifTplToAddrPrimaryAuthors()
        return nttapa

class NotifTplCondition(Persistent):
    """
    """

    def __init__(self):
        self._tpl=None
        self._id=-1

    def clone(self, template):
        con = NotifyCondition()
        con.includeInTpl(template)
        return con

    def delete(self):
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def includeInTpl(self,newTpl,newId):
        self._tpl=newTpl
        self._id=newId

    def getTpl(self):
        return self._tpl

    def getId(self):
        return self._id

    def satisfies(self,abs):
        return True


class NotifTplCondAccepted(NotifTplCondition):

    def __init__(self,track="--any--",contribType="--any--"):
        NotifTplCondition.__init__(self)
        self._track=track
        self._contribType=contribType

    def clone(self, conference, template):
        ntca = NotifTplCondAccepted()
        for newtrack in conference.getTrackList() :
            if newtrack.getTitle() == self.getTrack().getTitle() :
                ntca.setTrack(newtrack)
        for newtype in conference.getContribTypeList() :
             if newtype.getName() == self.getContribType() :
                ntca.setContribType(newtype)

        return ntca

    def setContribType(self, ct="--any--"):
        self._contribType = ct

    def getContribType(self):
        return self._contribType

    def setTrack(self, tr="--any--"):
        self._track = tr

    def getTrack(self):
        try:
            if self._track:
                pass
        except AttributeError:
            self._track="--any--"
        return self._track

    def _satifiesContribType(self,abs):
        status=abs.getCurrentStatus()
        if self._contribType=="--any--":
            return True
        else:
            if self._contribType=="" or self._contribType==None or \
                                            self._contribType=="--none--":
                return status.getType()=="" or status.getType()==None
            return status.getType()==self._contribType
        return False

    def _satifiesTrack(self,abs):
        status=abs.getCurrentStatus()
        if self.getTrack()=="--any--":
            return True
        else:
            if self.getTrack()=="" or self.getTrack() is None or \
                                            self.getTrack()=="--none--":
                return status.getTrack()=="" or status.getTrack()==None
            return status.getTrack()==self.getTrack()
        return False

    def satisfies(self,abs):
        if not isinstance(abs.getCurrentStatus(),AbstractStatusAccepted):
            return False
        else:
            return self._satifiesContribType(abs) and self._satifiesTrack(abs)


class NotifTplCondRejected(NotifTplCondition):

    def satisfies(self,abs):
        return isinstance(abs.getCurrentStatus(),AbstractStatusRejected)

    def clone(self, conference, template):
        ntcr = NotifTplCondRejected()
        ntcr.includeInTpl(template)
        return ntcr

class NotifTplCondMerged(NotifTplCondition):

    def satisfies(self,abs):
        return isinstance(abs.getCurrentStatus(),AbstractStatusMerged)

    def clone(self, conference, template):
        ntcm = NotifTplCondMerged()
        ntcm.includeInTpl(newTpl, newId)

class NotificationLog(Persistent):

    def __init__(self,abstract):
        self._abstract=abstract
        self._entries=PersistentList()

    def getAbstract(self):
        return self._abstract

    def addEntry(self,newEntry):
        if newEntry!=None and newEntry not in self._entries:
            self._entries.append(newEntry)

    def getEntryList(self):
        return self._entries

    # The 3 following metods are used only for recovery purposes:

    def removeEntry(self, entry):
        if entry!=None and entry in self._entries:
            self._entries.remove(entry)
            entry.delete()

    def recoverEntry(self, entry):
        self.addEntry(entry)
        entry.recover()

    def clearEntryList(self):
        while len(self.getEntryList()) > 0:
            self.removeEntry(self.getEntryList()[0])

    # -----------------------------------------------------------

class NotifLogEntry(Persistent):

    def __init__(self,responsible,tpl):
        self._setDate(nowutc())
        self._setResponsible(responsible)
        self._setTpl(tpl)

    def _setDate(self,newDate):
        self._date=newDate

    def getDate(self):
        return self._date

    def _setResponsible(self,newResp):
        self._responsible=newResp

    def getResponsible(self):
        return self._responsible

    def _setTpl(self,newTpl):
        self._tpl=newTpl

    def getTpl(self):
        return self._tpl

    def delete(self):
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)
