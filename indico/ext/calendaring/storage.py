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

from MaKaC.plugins import PluginsHolder
from BTrees.OOBTree import OOBTree
from MaKaC.user import Avatar
from indico.core.db import DBMgr
from persistent.list import PersistentList
from MaKaC.conference import Conference
from MaKaC.common.timezoneUtils import nowutc

"""
Here are included some general-purpose storage operations that are used from different parts
of the Calendaring module
"""


def getUserDisablePluginStorage():
    storage = PluginsHolder().getPluginType("calendaring").getStorage()
    if 'avatar_plugin_disable' not in storage:
        storage['avatar_plugin_disable'] = OOBTree()
    return storage['avatar_plugin_disable']


def enablePluginForUser(userId):
    storage = getUserDisablePluginStorage()
    if userId in storage:
        del storage[userId]


def disablePluginForUser(userId):
    storage = getUserDisablePluginStorage()
    storage[userId] = False


def isUserPluginEnabled(userId):
    storage = getUserDisablePluginStorage()
    return True if storage.get(str(userId)) == None else False


def getAvatarConferenceStorage():
    storage = PluginsHolder().getPluginType("calendaring").getStorage()
    if 'avatar_conference' not in storage:
        storage['avatar_conference'] = OOBTree()
    return storage['avatar_conference']


def addAvatarConference(avatar, conference, eventType):
    if conference.getStartDate() > nowutc():
        avatar = getAvatar(avatar)
        if avatar and isUserPluginEnabled(avatar.getId()):
            storage = getAvatarConferenceStorage()
            key = avatar.getId() + "_" + conference.getId()
            if not storage.get(key):
                storage[key] = PersistentList()
            # Remove duplicated events to avoid passing two identical pairs:
            # key + eventType to ExternalOperationsManager
            storage[key] = PersistentList([event for event in storage[key] if event['eventType'] != eventType])
            storage[key].append(dict(avatar=avatar, conference=conference, eventType=eventType))


def updateConference(obj, status="updated"):
    if isinstance(obj, Conference):
        for participant in obj.getParticipation().getParticipantList():
            avatar = participant.getAvatar()
            if avatar and isUserPluginEnabled(avatar.getId()) and participant.getStatus() == "added":
                addAvatarConference(avatar, obj, status)
        for registrant in obj.getRegistrantsList():
            avatar = registrant.getAvatar()
            if avatar and isUserPluginEnabled(avatar.getId()):
                addAvatarConference(avatar, obj, status)

def removeConference(obj):
    updateConference(obj, status="removed")

def getAvatar(avatar):
    if isinstance(avatar, Avatar):
        return avatar
    if hasattr(avatar, 'getAvatar'): # Participant, Registrant, etc.
        return avatar.getAvatar()
    return None
