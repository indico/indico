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
from MaKaC.plugins.util import PluginFieldsWrapper
from MaKaC.plugins.InstantMessaging.indexes import CounterIndex, IndexByConf, IndexByID, IndexByUser


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
    def getCounter(cls):
        root = cls.getChatRoot()

        if not root.has_key('counter'):
            raise ServiceError( message=_('Expected index not found while accessing the database (counter)'))

        return root['counter']

    @classmethod
    def newID(cls):
        #create it in case it doesn't exist
        return CounterIndex().get().newCount()
        #return cls.getCounter().newCount()

    @classmethod
    def getChatroomList(cls, conf):
        conf = str(conf.getId())
        index = IndexByConf(conf).get()

        if not index.has_key(conf):
            raise ServiceError( message=_('Conference not found in database: %s' %conf))
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
        index = IndexByUser(userID).get()

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



class LinkGenerator:
    """ Generates links to xmpp chat rooms """

    def __init__(self, chatroom):
        self._chatroom = chatroom

    def generate(self):
        pass

class WebLinkGenerator(LinkGenerator):

    def __init__(self, chatroom):
        LinkGenerator.__init__(self, chatroom)

    def generate(self, anonymous = False):
        if anonymous:
            return 'https://'+ self._chatroom.getHost()+ '/?r=' +self._chatroom.getTitle()+'@conference.'+self._chatroom.getHost()+'?join'
        else:
            return 'https://'+ self._chatroom.getHost()+ '/?x=' +self._chatroom.getTitle()+'@conference.'+self._chatroom.getHost()+'?join'

class DesktopLinkGenerator(LinkGenerator):

    def __init__(self, chatroom):
        LinkGenerator.__init__(self, chatroom)

    def generate(self):
        return 'xmpp:'+ self._chatroom.getTitle()+'@'+self._chatroom.getHost()+'?join'

class LogLinkGenerator(LinkGenerator):

    def __init__(self, chatroom):
        LinkGenerator.__init__(self, chatroom)

    def generate(self, sDate = None, eDate = None):
        dates = ''
        if sDate != None:
            dates = '&sdate='+sDate
        elif eDate != None:
            dates = '&edate='+eDate
        if eDate != None and sDate != None:
            dates += '&edate='+eDate
        return 'https://'+ \
                PluginFieldsWrapper('InstantMessaging', 'XMPP').getOption('chatServerHost') + \
                '/code.py/?cr=' + \
                self._chatroom.getTitle() + \
                '@conference.' + \
                self._chatroom.getHost() + \
                dates

class DeleteLogLinkGenerator(LinkGenerator):
    def __init__(self, chatroom):
        LinkGenerator.__init__(self, chatroom)

    def generate(self):
        return 'https://'+ \
                PluginFieldsWrapper('InstantMessaging', 'XMPP').getOption('chatServerHost') + \
                '/code.py/delete?cr=' + \
                self._chatroom.getTitle() + \
                '@conference.' + \
                self._chatroom.getHost()
