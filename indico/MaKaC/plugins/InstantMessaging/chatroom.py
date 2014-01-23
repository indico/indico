# -*- coding: utf-8 -*-
##
## $id$
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

from persistent import Persistent
from persistent.mapping import PersistentMapping
from pytz import timezone, all_timezones
from MaKaC.common.fossilize import Fossilizable, fossilizes, fossilize
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.common.Conversion import Conversion
from MaKaC.plugins.InstantMessaging.XMPP import fossils
from MaKaC.services.interface.rpc.common import ServiceError



class Chatroom(Persistent, Fossilizable):

    fossilizes(fossils.IChatRoomFossil)

    def __init__( self, name, owner, conference, modificationDate=None, createdInLocalServer=True, showRoom=False ):
        Persistent.__init__(self)
        self._name = name
        self._owner = owner
        self._creationDate = nowutc()
        self._conferences = PersistentMapping()
        self._conferences[conference.getId()] = conference
        self._modificationDate = modificationDate
        self._createdInLocalServer = createdInLocalServer
        self._showRoom = showRoom
        #the id will be assigned just before being stored in the DB.
        #If we try to create a counter now it will fail if it's the first chatroom
        #in the conference, since no indexes have been created yet
        self._id = None

    def __cmp__(self, obj):
        """ Needed to make internal comparisons in the OOTreeSet or OOBTree.
            Otherwise we may get some KeyErrors when trying to delete chat rooms.
            Ordered by title on insertion to speed up query slicing.
        """
        return cmp(self.getTitle().lower(), obj.getTitle().lower())

    def setValues(self, values):
        self._name = values['title']
        self._owner = values['user']
        #it has to be a dictionary with conferences, otherwise it'll make everything go wrong
        self._conferences[values['conference'].getId()] = values['conference']
        self._modificationDate = values['modificationDate']
        self._createdInLocalServer = values['createdInLocalServer']
        self._showRoom = values['showRoom']

    def setTitle(self, name):
        self._name = name

    def getTitle(self):
        return self._name

    def setOwner(self, owner):
        self._owner = owner

    def getOwner(self):
        return self._owner

    def setCreationDate(self, date):
        self._creationDate = date

    def getCreationDate(self):
        return self._creationDate

    def getAdjustedCreationDate(self,tz=None):
        if not tz or tz not in all_timezones:
            tz = 'UTC'
        return self.getCreationDate().astimezone(timezone(tz))

    def setCreatedInLocalServer(self, createdInLocalServer):
        self._createdInLocalServer = createdInLocalServer

    def getCreatedInLocalServer(self):
        return self._createdInLocalServer

    def setShowRoom(self, showRoom):
        self._showRoom = showRoom

    def getShowRoom(self):
        return self._showRoom

    def setModificationDate(self, date):
        self._modificationDate = date

    def getModificationDate(self):
        return self._modificationDate

    def getAdjustedModificationDate(self,tz=None):
        if not self.getModificationDate():
            return None
        if not tz or tz not in all_timezones:
            tz = 'UTC'
        return self.getModificationDate().astimezone(timezone(tz))

    def setConference(self, conference):
        self._conferences[conference.getId()] = conference

    def getConferences(self):
        return self._conferences

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def fossilizeMultiConference(self, conference):
        """Since we may have more than 1 conference for the same chat room we cannot know to which timezone should we adjust the dates when fossilizing.
        Therefore, we do it manually with the conference given in the request"""
        fossilizedRoom = self.fossilize()
        tz=conference.getTimezone()
        fossilizedRoom['creationDate'] = Conversion().datetime(self._creationDate.astimezone(timezone(tz)), tz)
        if self._modificationDate:
            fossilizedRoom['modificationDate'] = Conversion().datetime(self._modificationDate.astimezone(timezone(tz)), tz)
        return fossilizedRoom
