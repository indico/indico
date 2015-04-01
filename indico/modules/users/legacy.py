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

from persistent import Persistent

from indico.modules.user.models.users import User


class AvatarUserWrapper(Persistent):
    """
    Wrapper Avatar-like class that holds a DB-stored user.
    """
    def __init__(self, user_id):
        self.user_id = user_id
        if not self.user_id:
            raise KeyError("User with id '{}' not found".format(user_id))

    @property
    def user(self):
        return User.get(self.user_id)
    
    def getId(self):
        return str(self.user_id)

    def __repr__(self):
        return "<AvatarUserWrapper {}: {} ({})>".format(self.user.id, self.user.full_name. self.user.email)
