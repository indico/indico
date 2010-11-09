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
Here are included the listeners and other components that are part of the
`livesync` plugin type.
"""

# dependency libs
from zope.interface import implements

# indico imports
from indico.core.api import Component
from indico.core.api.category import ICategoryActionListener
from indico.core.api.conference import IEventActionListener
from indico.core.api.db import IDBUpdateListener, DBUpdateException
from indico.core.api.rh import IServerRequestListener
from indico.util.date_time import int_timestamp, nowutc

# plugin imports
from indico.ext.livesync.agent import ActionWrapper
from indico.ext.livesync.util import getPluginType
from indico.ext.livesync.agent import SyncManager

# legacy indico imports
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.logger import Logger

class LiveSyncCoreListener(Component):

    implements(IServerRequestListener,
               ICategoryActionListener,
               IEventActionListener)

    def _add(self, obj, actions):
        """
        Adds a provided object to the temporary index.
        Actions: ['moved','deleted',..]
        """
        cm_set = ContextManager.get('indico.ext.livesync:actions').setdefault(
            obj, set([]))
        cm_set |= set(actions)

    # IServerRequestListener
    def requestFinished(self, req):
        """
        Inserts the elements from the temporary index into the permanent one
        """

        track = SyncManager.getDBInstance().getTrack()
        cm = ContextManager.get('indico.ext.livesync:actions')

        timestamp = int_timestamp(nowutc())

        # if the returned context is a dummy one, there's nothinhg to do
        if cm.__class__ == ContextManager.DummyContext:
            return

        for obj, actions in cm.iteritems():
            for action in actions:
                Logger.get('ext.livesync').debug((obj, action))
                # TODO: remove redundant items
                track.add(timestamp, ActionWrapper(timestamp, obj, actions))

    def requestRetry(self, req, nretry):
        # reset the context manager
        ContextManager.set('indico.ext.livesync:actions', {})

    def requestStarted(self, req):
        # reset the context manager
        ContextManager.set('indico.ext.livesync:actions', {})

    # ICategoryActionListener
    def categoryMoved(self, category, oldOwner, newOwner):

        changes = ['moved']

        # protection status changed?
        if oldOwner.isProtected() != newOwner.isProtected():
            # notify protection change too
            changes += ['protection']

        self._add(category, changes)

    def _eventInfoChanged(self, event, what):
        self._add(event, ['%s_changed' % what])

    def _eventProtectionChanged(self, event):
        self._eventInfoChanged(event, 'protection')

    def eventDateChanged(self, event, params):
        self._eventInfoChanged(event, 'dates')

    def eventStartDateChanged(self, event, params):
        self._eventInfoChanged(event, 'start_date')

    def eventEndDateChanged(self, event, params):
        self._eventInfoChanged(event, 'end_date')

    def eventStartTimeChanged(self, event, sdate):
        self._eventInfoChanged(event, 'start_date')

    def eventEndTimeChanged(self, event, edate):
        self._eventInfoChanged(event, 'end_date')

    def eventTimezoneChanged(self, event, oldTZ):
        self._eventInfoChanged(event, 'timezone')

    def eventTitleChanged(self, event, params):
        self._eventInfoChanged(event, 'title')

    def eventDeleted(self, event, params):
        self._add(event, ['deleted'])
