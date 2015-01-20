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

from MaKaC.plugins.Collaboration.Vidyo.api.client import AdminClient, UserClient
from MaKaC.plugins.Collaboration.Vidyo.common import getVidyoOptionValue


class SOAPObjectFactory(object):
    """ This is a class with several class methods.
        Each class method creates a different kind of SOAP object.
        These SOAP objects are passed as arguments to the SOAP service calls.
        The methods also set default values for some attributes.
    """

    @classmethod
    def createRoom(cls, name, description, ownerName, extension, pin, moderatorPin):
        """ Creates a SOAP room object
        """
        vidyoClient = AdminClient.getInstance()

        newRoom = vidyoClient.factory.create('Room')
        newRoom.name = name
        newRoom.RoomType = 'Public'
        newRoom.ownerName = ownerName
        newRoom.extension = extension
        newRoom.groupName = getVidyoOptionValue("indicoGroup")
        newRoom.description = description
        newRoom.RoomMode.isLocked = False
        if pin:
            newRoom.RoomMode.hasPIN = True
            newRoom.RoomMode.roomPIN = pin
        else:
            newRoom.RoomMode.hasPIN = False

        if moderatorPin:
            newRoom.RoomMode.hasModeratorPIN = True
            newRoom.RoomMode.moderatorPIN = moderatorPin
        else:
            newRoom.RoomMode.hasModeratorPIN = False

        return newRoom

    @classmethod
    def createFilter(cls, apiType, query, entityType=None):
        if apiType == 'admin':
            vidyoClient = AdminClient.getInstance()
        else:
            vidyoClient = UserClient.getInstance()

        newFilter = vidyoClient.factory.create('Filter')
        newFilter.query = query
        newFilter.dir = 'DESC'
        if entityType:
            newFilter.EntityType = entityType

        return newFilter
