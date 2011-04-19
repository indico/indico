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

"""
DB Update and related matters

This should be easy to adapt to InTRePId 2, in the case of its acceptance.
"""

# plugin imports
from indico.ext.livesync.util import getPluginType
from indico.ext.livesync.agent import SyncManager
from indico.ext.livesync.base import MPT_GRANULARITY
from indico.core.extpoint.db import DBUpdateException


def updateDBStructures(root, granularity=MPT_GRANULARITY):
    """
    Updates the DB for use with livesync
    """

    # get our storage
    ptype = getPluginType()
    storage = ptype.getStorage()

    # check if it is empty
    if len(storage) == 0:
        # nice, let's fill it
        storage['agent_manager'] = SyncManager(granularity=granularity)
        return True

    else:
        raise Exception("This DB seems to already have livesync installed")
