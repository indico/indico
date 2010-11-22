# -*- coding: utf-8 -*-
##
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

# system imports
import contextlib

# ZODB imports
import ZODB
from ZODB import ConflictResolution, MappingStorage
import transaction

# legacy imports
from MaKaC.common.db import DBMgr
from MaKaC.conference import CategoryManager, DefaultConference

from MaKaC import user
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.common import HelperMaKaCInfo
from MaKaC.common.info import HelperMaKaCInfo

# indico imports
from indico.tests.python.unit.util import IndicoTestFeature


class TestMemStorage(MappingStorage.MappingStorage,
                     ConflictResolution.ConflictResolvingStorage):

    """
    Test memory storage - useful for conflicts
    """

    def __init__(self, name='foo'):
        MappingStorage.MappingStorage.__init__(self, name)
        ConflictResolution.ConflictResolvingStorage.__init__(self)

    @ZODB.utils.locked(MappingStorage.MappingStorage.opened)
    def store(self, oid, serial, data, version, transaction):
        assert not version, "Versions are not supported"
        if transaction is not self._transaction:
            raise ZODB.POSException.StorageTransactionError(self, transaction)

        old_tid = None
        tid_data = self._data.get(oid)
        if tid_data:
            old_tid = tid_data.maxKey()
            if serial != old_tid:
                data = self.tryToResolveConflict(oid, old_tid, serial, data)

        self._tdata[oid] = data

        return self._tid


class Database_Feature(IndicoTestFeature):
    """
    Connects/disconnects the database
    """

    _requires = []

    def start(self, obj):
        super(Database_Feature, self).start(obj)

        obj._dbi = DBMgr.getInstance()

        # Reset everything
        with obj._context('database'):
            conn = obj._dbi._getConnObject()
            r = conn.root._root

            for e in r.keys():
                del r[e]

            # initialize db root
            cm = CategoryManager()
            cm.getRoot()

            obj._home = cm.getById('0')

    def _action_startDBReq(obj):
        obj._dbi.startRequest()

    def _action_stopDBReq(obj):
        obj._dbi.endRequest()

    def _context_database(self):
        if DBMgr.getInstance().isConnected():
            yield
            return

        self._startDBReq()
        yield
        self._stopDBReq()


class DummyUser_Feature(IndicoTestFeature):

    """
    Creates a dummy user - needs database
    """

    _requires = ['db.Database']

    def start(self, obj):
        super(DummyUser_Feature, self).start(obj)
        with obj._context('database'):

            #filling info to new user
            avatar = user.Avatar()
            avatar.setName( "fake" )
            avatar.setSurName( "fake" )
            avatar.setOrganisation( "fake" )
            avatar.setLang( "en_US" )
            avatar.setEmail( "fake@fake.fake" )

            #registering user
            ah = user.AvatarHolder()
            ah.add(avatar)

            #setting up the login info
            li = user.LoginInfo( "dummyuser", "dummyuser" )
            ih = AuthenticatorMgr()
            userid = ih.createIdentity( li, avatar, "Local" )
            ih.add( userid )

            #activate the account
            avatar.activateAccount()

            #since the DB is empty, we have to add dummy user as admin
            minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
            al = minfo.getAdminList()
            al.grant( avatar )

            obj._dummy = avatar

            HelperMaKaCInfo.getMaKaCInfoInstance().setDefaultConference(DefaultConference())


