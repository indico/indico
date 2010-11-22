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
from indico.core.api.events import IAccessControlListener, IObjectLifeCycleListener, \
     IMetadataChangeListener
from indico.core.api.db import IDBUpdateListener, DBUpdateException
from indico.core.api.rh import IServerRequestListener
from indico.util.date_time import int_timestamp, nowutc

# plugin imports
from indico.ext.livesync.base import ActionWrapper
from indico.ext.livesync.util import getPluginType
from indico.ext.livesync.agent import SyncManager

# legacy indico imports
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.logger import Logger


class RequestListener(Component):

    implements(IServerRequestListener)

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


class ObjectChangeListener(Component):

    implements(IAccessControlListener,
               IObjectLifeCycleListener,
               IMetadataChangeListener)

    def _add(self, obj, actions):
        """
        Adds a provided object to the temporary index.
        Actions: ['moved','deleted',..]
        """
        cm_set = ContextManager.get('indico.ext.livesync:actions').setdefault(
            obj, set([]))

        cm_set |= set(actions)

    def _protectionChanged(self, obj, oldValue, newValue):
        """
        Generic method, independent of object type
        """
        if newValue == 0:
            # 0 is not an option,as remote services may not know anything
            # about categories (and 0 means 'inherited')
            newValue = 1 if obj.isProtected() else -1

        if oldValue == newValue:
            # protection didn't actually change
            return
        else:
            if newValue == -1:
                self._add(obj, ['set_public'])
            else:
                self._add(obj, ['set_private'])

    def _parentProtectionChanged(self, obj, oldValue, newValue):
        """
        This will normally be called when an event/subcategory is moved to a category
        with a different protection scheme
        """

        # take this into account only if inheriting from parent
        if obj.getAccessProtectionLevel() == 0:
            if newValue == 1:
                self._add(obj, ['set_private'])
            else:
                self._add(obj, ['set_public'])
        else:
            # nothing to do, move along
            pass

    def _objectInfoChanged(self, obj, what):
        self._add(obj, ['%s_changed' % what])

    # IObjectLifeCycleListener
    def moved(self, obj, fromOwner, toOwner):
        self._add(obj, ['moved'])

        categoryProtection = fromOwner.isProtected()
        newCategoryProtection = toOwner.isProtected()

        if categoryProtection != newCategoryProtection:
            self._parentProtectionChanged(obj, categoryProtection,
                                          newCategoryProtection)

    def created(self, obj, owner):
        self._objectInfoChanged(owner, 'data')
        self._add(obj, ['created'])

    def deleted(self, obj, oldOwner):
        self._add(obj, ['deleted'])

    # IMetadataChangeListener
    def titleChanged(self, obj, oldTitle, newTitle):
        self._objectInfoChanged(obj, 'title')

    def infoChanged(self, obj):
        self._objectInfoChanged(obj, 'data')

    # IAccessControlListener
    def protectionChanged(self, obj, oldProtection, newProtection):
        self._protectionChanged(obj, oldProtection, newProtection)

    def accessDomainAdded(self, obj, domain):
        self._objectInfoChanged(category, 'acl')

    def accessDomainRemoved(self, obj, domain):
        self._objectInfoChanged(category, 'acl')
