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

from MaKaC.common.Counter import Counter
from BTrees.OOBTree import OOBTree, OOTreeSet
from MaKaC.services.interface.rpc.common import ServiceError, NoReportError
from persistent import Persistent
from MaKaC.plugins.util import PluginFieldsWrapper
from MaKaC.i18n import _

class IMIndex(Persistent):

    def __init__(self, index, storingStructure=OOBTree, pluginId="XMPP"):
        self._root = PluginFieldsWrapper('InstantMessaging', pluginId).getStorage()
        self._index = index
        self._storingStructure = storingStructure
        self._indexCheck()

    def _indexCheck(self):
        """ If the index doesn't exist we'll need to create it. In case you don't understand this method
            take a pencil and a paper and draw the tree to get it. Do NOT change it without being completely
            sure of what you're doing!"""
        #if not self._root.has_key(self._index):
        #    self._root[self._index] = self._storingStructure()
        #self._indexToAccess = self._root[self._index]
        if not self._root.has_key(self._index):
            self._root[self._index] = self
            self._storingStructure = self._storingStructure()
        self._indexToAccess = self._root[self._index]
        self._storingStructure = self._indexToAccess.get()

    def _indexCheckDelete(self, element):
        #if len( self._root[self._index][element] ) is 0:
        #    self._root[self._index].pop(element)
        if len( self.get()[element] ) is 0:
            self.get().pop(element)


    def get(self):
        #return self._indexToAccess
        return self._storingStructure

    def index(self, element):
        pass

    def unindex(self, element):
        pass


class CounterIndex(IMIndex):
    """ This index just takes the count of the next index that shall be given to a new chat room """

    def __init__(self):
        IMIndex.__init__(self, 'counter', Counter)


class IndexByConf(IMIndex):
    """ Index by conference. Using the conference id as the key, there will be a OOTreeSet inside with all the existing chat rooms for that conference"""

    def __init__(self, conf):
        IMIndex.__init__(self, 'indexByConf')
        self._conf = conf

    def index(self, element):
        self._indexCheck()

        # self.get is equivalent to root['indexByConf']
        if not self.get().has_key(self._conf):
            self.get()[self._conf] = OOTreeSet()

        self.get()[self._conf].insert(element)

    def unindex(self, element):
        self.get()[self._conf].remove(element)

        self._indexCheckDelete(self._conf)


class IndexByUser(IMIndex):
    """ Index by user ID. We use a OOTreeSet to store the chat rooms"""

    def __init__(self, id):
        IMIndex.__init__(self, 'indexByUser')
        self._id = id

    def index(self, element):
        self._indexCheck()

        # self.get is equivalent to root['IndexByUser']
        if not self.get().has_key(self._id):
            self.get()[self._id] = OOTreeSet()

        self.get()[self._id].insert(element)

    def unindex(self, element):
        self.get()[self._id].remove(element)

        self._indexCheckDelete(self._id)


class IndexByCRName(IMIndex):
    """ Index by chat room name. We allow chat rooms to have the same name if they are in different servers. For each key we use a OOTreeSet to store them"""

    def __init__(self, name):
        IMIndex.__init__(self, 'indexByCRName')
        self._name = name

    def index(self, element):
        self._indexCheck()

        # self.get is equivalent to root['IndexByCRName']
        if self.get().has_key(element.getTitle()):
            for cr in self.get()[element.getTitle()]:
                #if there is a chat room repeated in the server (either ours or an external one) we have a problem
                if cr.getTitle() == element.getTitle() and cr.getHost() == element.getHost():
                    raise NoReportError( _('There is already a chat room in that server with that name, please choose another one'))
        else:
            self.get()[element.getTitle()] = OOTreeSet()

        self.get()[element.getTitle()].insert(element)

    def unindex(self, element, indexToRemove=''):
        #we may want to delete a different index of the one contained in the element
        #for example, for the chat room edition we want to delete the index of the
        #previous chat room name
        if indexToRemove != '':
            self.get()[indexToRemove].remove(element)
            self._indexCheckDelete(indexToRemove)
        else:
            self.get()[self._name].remove(element)
            self._indexCheckDelete(self._name)


class IndexByID(IMIndex):
    """ Index by chat room ID. Since there can only exist one index per chat room, for each key there will directly be the Chatroom object"""

    def __init__(self):
        IMIndex.__init__(self, 'indexByID')

    def index(self, element):
        self._indexCheck()

        # self.get is equivalent to root['IndexByID']
        if self.get().has_key(element.getId()):
            raise ServiceError( message=_('There is already a chat room with the same id'))

        self.get()[element.getId()] = element

    def unindex(self, element):
        self.get().pop(element.getId())

