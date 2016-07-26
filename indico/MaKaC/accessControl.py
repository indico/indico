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

from MaKaC.common.contextManager import ContextManager


class AccessWrapper:
    """This class encapsulates the information about an access to the system. It
            must be initialised by clients if they want to perform access
            control operations over the objects in the system.
    """

    def __init__(self, user=None):
        self._currentUser = user

    def setUser( self, newAvatar ):
        self._currentUser = newAvatar
        ContextManager.set('currentUser', self._currentUser)

    def getUser( self ):
        return self._currentUser

    @property
    def user(self):
        return self._currentUser.as_new if self._currentUser else None
