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
Here are included the listeners and other components that are part of the
`livesync` plugin type.
"""

# dependency libs
from zope.interface import implements

# indico imports
from indico.core.extpoint import Component
from indico.core.extpoint.events import IAccessControlListener, IObjectLifeCycleListener, \
     IMetadataChangeListener
from indico.core.extpoint.rh import IServerRequestListener
from indico.util.date_time import int_timestamp, nowutc
from indico.util.event import uniqueId

# plugin imports
from indico.ext.livesync.base import ActionWrapper
from indico.ext.livesync.agent import SyncManager

# legacy indico imports
from MaKaC.common.contextManager import ContextManager, DummyDict
from MaKaC.common.logger import Logger
from MaKaC import conference, accessControl


class RequestListener(Component):
    """
    This component manages the ``ContextManager`` area that stores
    livesync actions
    """

    implements(IServerRequestListener)

    # IServerRequestListener

    def requestFinished(self, obj):

        sm = SyncManager.getDBInstance()
        cm = ContextManager.get('indico.ext.livesync:actions')
        cm_ids = ContextManager.get('indico.ext.livesync:ids')

        timestamp = int_timestamp(nowutc())

        # if the returned context is a dummy one, there's nothing to do
        if cm.__class__ == DummyDict:
            return

        # Insert the elements from the temporary index
        # into the permanent one (MPT)
        for obj, actions in cm.iteritems():
            objId = cm_ids[obj]
            for action in actions:
                Logger.get('ext.livesync').debug((objId, action))
                # TODO: remove redundant items
            if not sm.objectExcluded(obj):
                sm.add(timestamp,
                       ActionWrapper(timestamp, obj, actions, objId))

    def requestRetry(self, obj, nretry):
        # reset the context manager
        ContextManager.set('indico.ext.livesync:actions', {})
        ContextManager.set('indico.ext.livesync:ids', {})

    def requestStarted(self, obj):
        # reset the context manager
        ContextManager.set('indico.ext.livesync:actions', {})
        ContextManager.set('indico.ext.livesync:ids', {})


class RequestListenerContext(object):
    """
    This class is mainly useful for testing or CLI scripting
    """
    def __init__(self):
        self._reqListener = RequestListener()

    def __enter__(self):
        self._reqListener.requestStarted(None)

    def __exit__(self, exc_type, exc_value, traceback):
        self._reqListener.requestFinished(None)


class ObjectChangeListener(Component):
    """
    This component listens for events and directs them to the MPT.
    Implements ``IAccessControlListener``, ``IObjectLifeCycleListener``
    and ``IMetadataChangeListener``
    """

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

        # the context may not be initialized
        if cm_set != None:
            cm_set |= set(actions)
        uid = uniqueId(obj)
        if uid is not None and uid != '':
            ContextManager.get('indico.ext.livesync:ids').setdefault(
                obj, uid)

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
    def _titleChanged(self, obj, oldTitle, newTitle):
        self._objectInfoChanged(obj, 'title')

    def categoryTitleChanged(self, obj, oldTitle, newTitle):
        self._titleChanged(obj, oldTitle, newTitle)

    def eventTitleChanged(self, obj, oldTitle, newTitle):
        self._titleChanged(obj, oldTitle, newTitle)

    def contributionTitleChanged(self, obj, oldTitle, newTitle):
        self._titleChanged(obj, oldTitle, newTitle)

    def infoChanged(self, obj):
        self._objectInfoChanged(obj, 'data')

    # IAccessControlListener
    def protectionChanged(self, obj, oldProtection, newProtection):
        self._protectionChanged(obj, oldProtection, newProtection)

    def _aclChanged(self, obj, child=False):
        """
        Emit right events, depending on whether a new record should be produced
        for the object or for a parent of it
        """
        if type(obj) in [conference.Conference, conference.Contribution,
                         conference.SubContribution, conference.Category]:
            # if it was a child, emit data_changed instead
            if child:
                self._objectInfoChanged(obj, 'data')
            else:
                self._objectInfoChanged(obj, 'acl')
        elif isinstance(obj, conference.Session):
            # TODO: Handle sessions properly, scheduling them for update
            # (contained contributions should be sent to server instead of whole event)
            owner = obj.getOwner()
            if owner:
                self._objectInfoChanged(owner, 'data')
            # else, do nothing, as it has probably been deleted
        elif isinstance(obj, accessControl.AccessController):
            self._aclChanged(obj.getOwner(), child=False)
        else:
            self._aclChanged(obj.getOwner(), child=True)

    def accessGranted(self, obj, who):
        self._aclChanged(obj)

    def accessRevoked(self, obj, who):
        self._aclChanged(obj)

    def modificationGranted(self, obj, who):
        self._aclChanged(obj)

    def modificationRevoked(self, obj, who):
        self._aclChanged(obj)

    def accessDomainAdded(self, obj, domain):
        self._objectInfoChanged(obj, 'acl')

    def accessDomainRemoved(self, obj, domain):
        self._objectInfoChanged(obj, 'acl')
