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

import ZODB
from ZODB import ConflictResolution, MappingStorage
import transaction


class TestMemStorage(MappingStorage.MappingStorage,
                     ConflictResolution.ConflictResolvingStorage):

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
