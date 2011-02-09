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
Livesync is an Indico plugin that allows information to be exported to other
systems in a regular basis, and to keep track of what has been exported.
It relies on "agents", basically interfaces that convert Indico metadata into
some format that can be read by the target system, and negociate the protocol
for data delivery.
"""

__metadata__ = {
    'name': "Live Sync",
    'description': "Synchronizes information between Indico and external repositories"
    }

from indico.ext.livesync.agent import PushSyncAgent, SyncAgent, SyncManager
from indico.ext.livesync.base import ActionWrapper

