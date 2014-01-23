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

from indico.core.extpoint import IListener

class IInstantMessagingListener(IListener):
    """ Inserts or deletes objects related to plugins in the DB. To do so, it retrieves the _storage parameter of the Plugin class,
        and then it inserts it in the DB according to the selected index policy """

    def createChatroom(self, obj, params):
        pass

    def editChatroom(self, obj, params):
        pass

    def deleteChatroom(self, obj, params):
        pass

    def addConference2Room(self, obj, params):
        """ When someone wants to re use a chat room for a different conference we need to add the conference
            to the conferences list in the chat room, but also to add the chat room in the IndexByConf index """
