# -*- coding: utf-8 -*-
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

from MaKaC.common.fossilize import IFossil
from MaKaC.common.Conversion import Conversion
from MaKaC.fossils.user import IAvatarFossil
from MaKaC.fossils.conference import IConferenceMinimalFossil


class IChatRoomFossil(IFossil):

    def getTitle(self):
        """ Returns the conference's title"""

    def getId(self):
        """ Returns the chat room's id"""
    #getId.convert = Conversion.counter

    def getCreatedInLocalServer(self):
        """ Returns if a new room has been created or just a url was added"""

    def getConferences(self):
        """ Returns the conference that the chat room belongs to"""
    getConferences.result = IConferenceMinimalFossil

    def getShowRoom(self):
        """ Returns if we want to hide the room or not """

    def getOwner(self):
        """ Returns the creator of the room """
    getOwner.result = IAvatarFossil

    def getAdjustedCreationDate(self):
        """ Date of creation of the chat room """
    getAdjustedCreationDate.convert = Conversion.datetime
    getAdjustedCreationDate.name = 'creationDate'

    def getAdjustedModificationDate(self):
        """ Date of modification of the chat room """
    getAdjustedModificationDate.convert = Conversion.datetime
    getAdjustedModificationDate.name = 'modificationDate'


class IXMPPChatRoomFossil(IChatRoomFossil):

    def getDescription(self):
        """ Returns the conference's description"""

    def getPassword(self):
        """ Returns the conference's password in case it's protected"""

    def getShowPass(self):
        """ Returns if we want to show the password in the event page or not """

    def getHost(self):
        """ Returns the host in case no new room was created """
