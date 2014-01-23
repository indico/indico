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

"""This file contain the definition of those classes which implement the root
access to the objects in the DB. The system will fetch and add objects to the
collections (or holders) through these classes that interact directly with the
persistence layer and do the necessary operations behind to ensure the
persistence.
"""
from BTrees import OOBTree

from indico.core.db import DBMgr
from Counter import Counter
from MaKaC.errors import MaKaCError

class ObjectHolder:
    """This class provides a common entry point for accessing conferences and
       other objects of the business layer encapsulating the access to the DB
       so it's transparent for other objects to deal with it.
       "Clients" will just instantiate this class and will retrieve the objects
       they are interested in through one of its methods. The object will have
       to manage to connect to the DB in the correct way and return the object
       the client asks for.
       This class is actually only a wrapper for the containers of objects,
       therefore it doesn't need to be persistent; it encapsulates the
       recovering and storing of those containers in the DB in a transparent
       way.
       Attributes:
        __allowedIdxs -- (List) Contains the names of the allowed indexes to be
            created in the DB
        idxName -- (string) Contains the name of the current index being wrapped
        counterName -- (string) Name of the counter which will be used to
            generate unique identifiers for the objects stored on the current
            index.
    """
    __allowedIdxs = ["conferences", "avatars", "groups", "counters",
                     "identities", "principals", "categories",
                     "localidentities", "groupsregistration",
                     "ldapidentities", "fieldsregistration", "registrationform",
                     "domains", "indexes", "trashcan", "roomsmapping",
                     "deletedobject", "shorturl", "modules", "plugins", "apikeys",
                     "consumers", "access_tokens", "request_tokens", "temp_request_tokens"]
    idxName = None
    counterName = None

    def __init__(self):
        """Class constructor. Gets an opened DB storage and initializes the
           DB connection so it's available for later requests.
        """
        self._idx = None

    def _setIdx( self ):
        if self.idxName == None:
            raise Exception( _("index name not set (%s)")%self.__class__.__name__)
        self._idx = self._getTree( self.idxName )

    def _getIdx( self ):
        """Returns the holder/catalog where all the objects are stored"""
        if self._idx == None:
            self._setIdx()
        return self._idx

    def _getTree(self, name):
        """Returns a OOBTree object stored in the DB root under the key "name".
           If the key doesn't exist if creates a new tree and inserts it into the
           DB root.
           BTree objects act as a dictionary but due to their data structure
           properties allow to increase the concurrency (don't need to load all
           the mapping on memory) and improves performance.
            Params:
                name -- key value of the requested tree
        """
        root = DBMgr.getInstance().getDBConnection().root()
        name =  name.lower()
        if not (name in self.__allowedIdxs):
            raise Exception( _("index name not allowed %s")%name)
        if not root.has_key( name ):
            root[ name ] = OOBTree.OOBTree()
        return root[ name ]

    def _newId( self ):
        """
        """
        if self.counterName == None:
            raise Exception( _("counter name not set (%s)")%self.__class__.__name__)
        idxs = self._getTree("counters")
        if not idxs.has_key(self.counterName):
            idxs[self.counterName] = Counter()
        return idxs[self.counterName].newCount()

    def getLastId(self):
        if self.counterName == None:
            raise Exception( _("counter name not set (%s)")%self.__class__.__name__)
        idxs = self._getTree("counters")
        if not idxs.has_key(self.counterName):
            idxs[self.counterName] = Counter()
        return idxs[self.counterName]._getCount()

    def add( self, newItem ):
        """adds an object to the index and assings it a new unique id.
        """
        if newItem.getId() != None and  newItem.getId() != "":
            #raise MaKaCError("Object %s has already an id it is probably already inserted in the holder %s"%(newItem, self.__class__))
            id = newItem.getId() # Used in recovery.
        else:
            id = str(self._newId())
            newItem.setId( id )
        tree = self._getIdx()
        tree[id] = newItem
        return id

    def remove( self, item ):
        """removes the specified object from the index.
        """
        tree = self._getIdx()
        if not tree.has_key( item.getId() ):
            return
        del tree[item.getId()]

    def removeById( self, itemid ):
        """removes the specified object from the index.
        """
        tree = self._getIdx()
        if not tree.has_key( itemid ):
            return
        del tree[itemid]

    def getById( self, id ):
        """returns an object from the index which id corresponds to the one
            which is specified.
        """
        return self._getIdx()[str(id)]

    def hasKey( self, id ):
        return self._getIdx().has_key( id )

    def getList( self ):
        """returns a list of all the objects which are inserted in the index
        """
        return self._getIdx().values()

    def getValuesToList( self ):
        l = []
        for i in self._getIdx().values():
            l.append(i)
        return l


class IndexHolder( ObjectHolder ):
    """Specialised ObjectHolder class which provides a wrapper for collections
        based in a Catalog for indexing the objects. It allows to index some
        declared attributes of the stored objects and then perform SQL-like
        queries
    """
    idxClass = None
    idFieldLabel = "id"

    def _setIdx( self ):
        if self.idxClass == None:
            raise Exception( _("index class not set (%s)")%self.__class__.__name__)
        shelf = DBMgr.getInstance().getDBConnection()
        #XXX: calling this provokes a modification on the shelf which produces
        #   read conflicts
        #self._idx = shelf.create_catalog( self.idxClass )
        if shelf.has_catalog( self.idxClass ):
            self._idx = shelf.get_catalog( self.idxClass )
        else:
            self._idx = shelf.create_catalog( self.idxClass )
        #try:
        #    self._idx = shelf.get_catalog( self.idxClass )
        #except KeyError, e:
        #    self._idx = Catalog( self.idxClass )
        #    shelf.add_catalog(self._idx)

    def add( self, newItem):
        #XXX: this makes the perfomance decrease dramatically. Operations like
        #   this should be avoided and the clients should now take care of
        #   not inserting the same user twice
        #if newItem in self.getList():
        #    return
        if newItem.getId() != None and  newItem.getId() != "":
            raise MaKaCError( _("Object %s has already an id it is probably already inserted in the holder %s")%(newItem, self.__class__))
        id = self._newId()
        newItem.setId( id )
        self._getIdx().insert( newItem )
        return id

    def remove( self, item ):
        self._getIdx().delete( item )

    def getById( self, id ):
        idx = self._getIdx()
        res = idx.query( "%s == '%s'"%(self.idFieldLabel, id ) )
        return res[0]

    def getList( self ):
        return self._getIdx().dump()

    def hasKey( self, id ):
        #XXX: verify how to implement it
        return False



