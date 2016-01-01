# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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


class MockConferenceHolder:
    # This class is monkeypatched on top of the real conferenceholder
    _events = {}

    def __init__(self):
        pass

    @classmethod
    def add(cls, event, creator=None):
        if event.id in cls._events:
            __tracebackhide__ = True
            raise Exception("Event '{}' already exists".format(event.id))
        cls._events[int(event.id)] = event

    @classmethod
    def remove(cls, event):
        del cls._events[int(event.id)]

    @classmethod
    def getById(cls, id_, quiet=None):
        if id_ is None:
            return None
        return cls._events.get(int(id_))


class MockConference(object):
    def __repr__(self):
        return '<MockConference({})>'.format(self.id)

    def getId(self):
        return self.id

    def getConference(self):
        return self

    def getOwner(self):
        try:
            return self.category
        except AttributeError:
            return None

    def log(self, *args, **kwargs):
        pass
