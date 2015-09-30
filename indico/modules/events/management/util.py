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

from indico.util.event import unify_event_args
from indico.util.user import unify_user_args


@unify_user_args
@unify_event_args(legacy=True)
def can_lock(event, user):
    """Checks whether a user can lock/unlock an event."""
    if not user:
        return False
    elif user.is_admin:
        return True
    elif user == event.as_event.creator:
        return True
    else:
        return any(cat.canUserModify(user.as_avatar) for cat in event.getOwnerList())
