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

from __future__ import unicode_literals

import bcrypt


class BCryptPassword(object):
    def __init__(self, hash_):
        self.hash = hash_

    def __eq__(self, value):
        if not self.hash:
            return False
        return self.hash == bcrypt.hashpw(value, self.hash)

    def __hash__(self):
        return hash(self.hash)

    def __repr__(self):
        return '<BCryptPassword({})>'.format(self.hash)

    @staticmethod
    def hash(value):
        return bcrypt.hashpw(value, bcrypt.gensalt())


class PasswordProperty(object):
    """Defines a hashed password property.

    When reading this property, it will return an object which will
    let you use the ``==`` operator to compare  the password against
    a plaintext password.  When assigning a value to it, it will be
    hashed and stored in :attr:`attr` of the containing object.

    :param attr: The attribute of the containing object where the
                 password hash is stored.
    :param backend: The password backend that handles hashing/checking
                    passwords.
    """

    def __init__(self, attr, backend=BCryptPassword):
        self.attr = attr
        self.backend = backend

    def __get__(self, instance, owner):
        return self.backend(getattr(instance, self.attr, None))

    def __set__(self, instance, value):
        setattr(instance, self.attr, self.backend.hash(value))

    def __delete__(self, instance):
        setattr(instance, self.attr, None)
