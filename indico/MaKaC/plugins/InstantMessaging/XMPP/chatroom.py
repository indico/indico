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

from MaKaC.common.fossilize import fossilizes
from MaKaC.plugins.InstantMessaging.XMPP import fossils
from MaKaC.plugins.InstantMessaging.chatroom import Chatroom



class XMPPChatroom(Chatroom):

    fossilizes(fossils.IXMPPChatRoomFossil)

    def __init__( self, name, owner, conference, modificationDate=None, description='',createdInLocalServer=True, host='', password='', showRoom=False, showPass=False ):
        Chatroom.__init__(self, name, owner, conference, modificationDate, createdInLocalServer, showRoom)
        self._description = description
        self._host = host
        self._password = password
        self._showPass = showPass

    def setValues(self, values):
        Chatroom.setValues(self, values)
        self._description = values['description']
        self._host = values['host']
        self._password = values['password']
        self._showPass = values['showPass']

    def setHost(self, host):
        self._host = host

    def getHost(self):
        return self._host

    def setDescription(self, description):
        self._description = description

    def getDescription(self):
        return self._description

    def setPassword(self, password):
        self._password = password

    def getPassword(self):
        return self._password

    def setShowPass(self, showPass):
        self._showPass = showPass

    def getShowPass(self):
        return self._showPass
