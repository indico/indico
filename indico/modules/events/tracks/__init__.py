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

from __future__ import unicode_literals

from indico.core.logger import Logger
from indico.core import signals
from indico.modules.events import Event


logger = Logger.get('tracks')


@signals.acl.can_access.connect_via(Event)
def _can_access_event(cls, obj, user, authorized, **kwargs):
    """Give track reviewers access to the event"""
    if not user or authorized is None or authorized:
        return
    avatar = user.as_avatar
    if any(track.isCoordinator(avatar) for track in obj.as_legacy.getTrackList()):
        return True
