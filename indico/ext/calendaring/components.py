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
Here are included the listeners that are part of the `calendaring` plugin type.
"""

from zope.interface import implements
from MaKaC.plugins import Observable
from indico.core.extpoint import Component
from indico.core.extpoint.events import ITimeActionListener, IMetadataChangeListener, IObjectLifeCycleListener
from indico.core.extpoint.location import ILocationActionListener
from indico.ext.calendaring.listeners import IRegistrantListener
from indico.ext.calendaring.storage import addAvatarConference, updateConference, removeConference


class RegistrantListener(Component, Observable):

    """
    Listen for event's that should trigger change in user calendar
    """

    implements(IRegistrantListener, ITimeActionListener,
               ILocationActionListener, IMetadataChangeListener, IObjectLifeCycleListener)

    def registrantAdded(self, conference, avatar):
        addAvatarConference(avatar, conference, 'added')

    def registrantRemoved(self, conference, avatar):
        addAvatarConference(avatar, conference, 'removed')

    def participantAdded(self, obj, conference, avatar):
        addAvatarConference(avatar, conference, 'added')

    def participantRemoved(self, obj, conference, avatar):
        addAvatarConference(avatar, conference, 'removed')

    def eventTitleChanged(self, obj, oldTitle, newTitle):
        updateConference(obj)

    def eventDescriptionChanged(self, obj, oldDesription, newDescription):
        updateConference(obj)

    def dateChanged(self, obj, params={}):
        updateConference(obj)

    def startDateChanged(self, obj, params={}):
        updateConference(obj)

    def endDateChanged(self, obj, params={}):
        updateConference(obj)

    def placeChanged(self, obj):
        updateConference(obj)

    def deleted(self, obj, oldOwner):
        removeConference(obj)
