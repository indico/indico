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

"""
DB Update and related matters

This should be easy to adapt to InTRePId 2, in the case of its acceptance.
"""

# plugin imports

from indico.ext.livesync.base import MPT_GRANULARITY


def updateDBStructures(root, granularity=MPT_GRANULARITY):
    """
    Updates the DB for use with livesync
    """

    from indico.ext.livesync.util import getPluginType
    from indico.ext.livesync.agent import SyncManager

    # get our storage
    ptype = getPluginType()
    storage = ptype.getStorage()

    # check if it is empty
    if 'agent_manager' in storage:
        raise Exception("This DB seems to already have livesync installed")
    else:
        # nice, let's fill it
        storage['agent_manager'] = SyncManager(granularity=granularity)
        return True
