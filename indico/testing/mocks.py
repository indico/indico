# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.


class MockAvatarHolder:
    # This class is monkeypatched on top of the real avatar holder
    _avatars = {}

    def __init__(self):
        pass

    @classmethod
    def add(cls, avatar):
        if avatar.id in cls._avatars:
            __tracebackhide__ = True
            raise Exception("Avatar '{}' already exists".format(avatar.id))
        cls._avatars[avatar.id] = avatar

    @classmethod
    def remove(cls, avatar):
        del cls._avatars[avatar.id]

    @classmethod
    def getById(cls, id_):
        return cls._avatars.get(id_)


class MockAvatar(object):
    def __repr__(self):
        return '<MockAvatar({})>'.format(self.id)

    def getEmail(self):
        return self.email

    def getEmails(self):
        return [self.email]

    def getFirstName(self):
        return self.name

    def getFullName(self):
        return '{}, {}'.format(self.surname.upper(), self.name)

    def getId(self):
        return self.id

    def isRBAdmin(self):
        return self.rb_admin

    def is_member_of_group(self, group_name):
        return group_name in self.groups

    def containsUser(self, avatar):
        return avatar == self


class MockGroupHolder:
    # This class is monkeypatched on top of the real group holder
    _groups = {}

    def __init__(self):
        pass

    @classmethod
    def add(cls, group):
        if group.id in cls._groups:
            __tracebackhide__ = True
            raise Exception(u"Group '{}' already exists".format(group.id))
        cls._groups[group.id] = group

    @classmethod
    def remove(cls, group):
        del cls._groups[group.id]

    @classmethod
    def getById(cls, id_):
        return cls._groups.get(id_)


class MockGroup(object):
    def __repr__(self):
        return '<MockGroup({})>'.format(self.id)

    def containsUser(self, avatar):
        return self.id in avatar.groups


class MockConferenceHolder:
    # This class is monkeypatched on top of the real conferenceholder
    _events = {}

    def __init__(self):
        pass

    @classmethod
    def add(cls, event):
        if event.id in cls._events:
            __tracebackhide__ = True
            raise Exception("Event '{}' already exists".format(event.id))
        cls._events[event.id] = event

    @classmethod
    def remove(cls, event):
        del cls._events[event.id]

    @classmethod
    def getById(cls, id_):
        return cls._events.get(id_)


class MockConference(object):
    def __repr__(self):
        return '<MockConference({})>'.format(self.id)

    def getId(self):
        return self.id
