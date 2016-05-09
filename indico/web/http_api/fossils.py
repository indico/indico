# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

"""
Basic fossils for data export
"""

from hashlib import md5

from indico.modules.attachments.api.util import build_material_legacy_api_data, build_folders_api_data
from indico.modules.events.notes.util import build_note_api_data
from indico.util.fossilize import IFossil
from indico.util.fossilize.conversion import Conversion
from MaKaC.webinterface import urlHandlers


class IHTTPAPIErrorFossil(IFossil):
    def getMessage(self):
        pass


class IHTTPAPIResultFossil(IFossil):
    def getTS(self):
        pass
    getTS.name = 'ts'

    def getURL(self):
        pass
    getURL.name = 'url'

    def getResults(self):
        pass


class IHTTPAPIExportResultFossil(IHTTPAPIResultFossil):
    def getCount(self):
        pass

    # New SQL-based hooks do not use it anymore, so we deprecate it for everything.
    # def getComplete(self):
    #     pass

    def getAdditionalInfo(self):
        pass


class IPeriodFossil(IFossil):
    def startDT(self):
        pass
    startDT.convert = Conversion.datetime

    def endDT(self):
        pass
    endDT.convert = Conversion.datetime


class ICategoryMetadataFossil(IFossil):
    def getId(self):
        pass

    def getName(self):
        pass

    def getLocator(self):
        pass
    getLocator.convert = Conversion.url(urlHandlers.UHCategoryDisplay)
    getLocator.name = 'url'


class ICategoryProtectedMetadataFossil(ICategoryMetadataFossil):
    def getName(self):
        pass
    getName.produce = lambda x: None


class IConferenceChairMetadataFossil(IFossil):

    def getId(self):
        pass

    def getFullName(self):
        pass

    def getEmail(self):
        pass
    getEmail.onlyIf = 'canModify'

    def getEmailHash(self):
        pass
    getEmailHash.produce = lambda s: md5(s.getEmail()).hexdigest()

    def getAffiliation(self):
        pass




class _IncludeMaterialFossil(IFossil):

    def getMaterial(self):
        pass
    getMaterial.produce = build_material_legacy_api_data
    getMaterial.convert = Conversion.addLegacyMinutes

    def getFolders(self):
        pass
    getFolders.produce = build_folders_api_data


class _IncludeACLFossil(IFossil):

    def getRecursiveAllowedToAccessList(self):
        pass
    getRecursiveAllowedToAccessList.produce = Conversion.allowedList
    getRecursiveAllowedToAccessList.name = 'allowed'
    getRecursiveAllowedToAccessList.onlyIf = 'canModify'


class IConferenceMetadataFossil(_IncludeMaterialFossil, _IncludeACLFossil, IFossil):

    def getId(self):
        pass

    def getStartDate(self):
        pass
    getStartDate.convert = Conversion.datetime

    def getEndDate(self):
        pass
    getEndDate.convert = Conversion.datetime

    def getTitle(self):
        pass

    def getDescription(self):
        pass

    def getType(self):
        pass

    def getOwner(self):
        pass
    getOwner.convert = lambda x: x.getTitle()
    getOwner.name = 'category'

    def getCategoryId(self):
        pass
    getCategoryId.produce = lambda x: x.getOwner().getId()

    def getTimezone(self):
        pass

    def getNote(self):
        pass
    getNote.produce = lambda x: build_note_api_data(x.note)

    def getChairList(self):
        pass
    getChairList.name = 'chairs'
    getChairList.result = IConferenceChairMetadataFossil

    def getLocation(self):
        """ Location (CERN/...) """
    getLocation.convert = lambda l: l and l.getName()

    def getLocator(self):
        pass
    getLocator.convert = Conversion.url(urlHandlers.UHConferenceDisplay)
    getLocator.name = 'url'

    def getRoom(self):
        """ Room (inside location) """
    getRoom.convert = lambda r: r and r.getName()

    def getRoomFullName(self):
        """ Conference Room """
    getRoomFullName.produce = lambda c: c.getRoom()
    getRoomFullName.convert = Conversion.roomFullName
    getRoomFullName.name = 'roomFullname'

    def getVisibility(self):
        pass
    getVisibility.name = 'visibility'
    getVisibility.produce = lambda x: Conversion.visibility(x)

    def hasAnyProtection(self):
        pass

    def getAddress(self):
        pass

    def getCreator(self):
        pass
    getCreator.produce = lambda x: x.as_event.creator.as_avatar
    getCreator.result = IConferenceChairMetadataFossil

    def getCreationDate(self):
        pass

    def getModificationDate(self):
        pass

    def getRoomMapURL(self):
        pass
    getRoomMapURL.produce = lambda x: x.as_event.room.map_url if x.as_event.room else None


class IBasicConferenceMetadataFossil(IFossil):

    def getId(self):
        pass

    def getStartDate(self):
        pass
    getStartDate.convert = Conversion.datetime

    def getEndDate(self):
        pass
    getEndDate.convert = Conversion.datetime

    def getTitle(self):
        pass

    def getType(self):
        pass

    def getOwner(self):
        pass
    getOwner.convert = lambda x: x.getTitle()
    getOwner.name = 'category'

    def getCategoryId(self):
        pass
    getCategoryId.produce = lambda x: x.getOwner().getId()

    def getLocator(self):
        pass
    getLocator.convert = Conversion.url(urlHandlers.UHConferenceDisplay)
    getLocator.name = 'url'
