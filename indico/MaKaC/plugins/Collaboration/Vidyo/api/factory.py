# -*- coding: utf-8 -*-
##
## $Id: options.py,v 1.2 2009/04/25 13:56:05 dmartinc Exp $
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

from MaKaC.plugins.Collaboration.Vidyo.api.client import AdminClient, UserClient
from MaKaC.plugins.Collaboration.Vidyo.common import getVidyoOptionValue


class SOAPObjectFactory(object):
    """ This is a class with several class methods.
        Each class method creates a different kind of SOAP object.
        These SOAP objects are passed as arguments to the SOAP service calls.
        The methods also set default values for some attributes.
    """

    @classmethod
    def createRoom(cls, name, description, ownerName, extension, pin):
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
            newRoom.RoomMode.hasPin = True
            newRoom.RoomMode.roomPIN = pin
        else:
            newRoom.RoomMode.hasPin = False

        return newRoom

    @classmethod
    def createFilter(cls, apiType, query):
        if apiType == 'admin':
            vidyoClient = AdminClient.getInstance()
        else:
            vidyoClient = UserClient.getInstance()

        newFilter = vidyoClient.factory.create('Filter')
        newFilter.query = query

        return newFilter
