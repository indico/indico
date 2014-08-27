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
## along with Indico; if not, see <http://www.gnu.org/licenses/>.


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
        return cls._avatars[id_]


class MockAvatar(object):
    def __repr__(self):
        return '<MockAvatar({})>'.format(self.id)
