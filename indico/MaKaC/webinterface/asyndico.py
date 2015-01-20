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

from MaKaC.common.fossilize import fossilize


class UserDataGenerator(object):

    def generate(self):
        """
        To be overridden
        """

    def __init__(self, user):
        self._user = user

class UserDataFavoriteUserListGenerator(UserDataGenerator):
    """
    """

    def generate(self):
        return fossilize(self._user.getPersonalInfo().getBasket().getUsers())

class UserDataFavoriteUserIdListGenerator(UserDataGenerator):
    """
    """

    def generate(self):
        return dict((userId, True) for userId in
                    self._user.getPersonalInfo().getBasket().getUsers())


class UserDataFactory(object):
    """
    Registers the different types of user data that
    might be needed for the client-side
    """

    # Any new "user data packages" should be added here
    _registry = {
        'favorite-user-list': UserDataFavoriteUserListGenerator,
        'favorite-user-ids': UserDataFavoriteUserIdListGenerator
        }

    def build(self, packageName):
        return self._registry[packageName](self._user).generate()

    def __init__(self, user):
        self._user = user

