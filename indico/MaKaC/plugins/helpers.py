# -*- coding: utf-8 -*-
##
## $id$
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

from MaKaC.common.logger import Logger
from MaKaC.services.interface.rpc.common import ServiceError, NoReportError
from MaKaC.webinterface import urlHandlers
from MaKaC.plugins.InstantMessaging.indexes import CounterIndex, IndexByConf, IndexByID, IndexByUser
from MaKaC.i18n import _

import string

class MailHelper:
    def __init__(self):
        self.__mails = []

    def newMail(self, function, *args):
        self.__mails.append({'function': function, 'args': args})
        return self.__mails

    def sendMails(self):
        for mail in self.__mails:
            mail['function'](*mail['args'])
        return True

class DBHelpers:

    @classmethod
    def newID(cls):
        return CounterIndex().get().newCount()

    @classmethod
    def getChatroomList(cls, conf):
        conf = str(conf.getId())
        index = IndexByConf().get()

        if not index.has_key(conf):
            return []
            # raise ServiceError( message=_('Conference not found in database: %s' %conf))
        return index[conf]

    @classmethod
    def getChatroom(cls, id):
        index = IndexByID().get()

        if not index.has_key(id):
            raise ServiceError( message=_('Chat room not found in database: %s' %id))
        return index[id]

    @classmethod
    def getRoomsByUser(cls, user):
        """ Will return the chat rooms created by the requested user """
        userID = str(user['id'])
        index = IndexByUser().get()

        if not index.has_key(userID):
            return []
        return index[userID]

    @classmethod
    def roomsToShow(cls, conf):
        """ For the given conference, will return True if there is any chat room to be shown
            in the conference page, and will return False if there are not
        """
        try:
            chatrooms = cls.getChatroomList(conf)
        except Exception,e:
            return False
        #there are no chatrooms, there's nothing to show
        if len(chatrooms) is 0:
            return False
        for chatroom in chatrooms:
            if chatroom.getShowRoom():
                return True
        #all the rooms were set to be hidden from the users
        return False

    @classmethod
    def getShowableRooms(cls, conf):
        chatrooms = []
        try:
            for room in cls.getChatroomList(conf):
                if room.getShowRoom():
                    chatrooms.append(room)
        except Exception,e:
            return []
        return chatrooms
